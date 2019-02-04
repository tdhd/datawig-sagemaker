import os
from io import StringIO

import flask
import pandas as pd
from datawig import SimpleImputer
import json

import cProfile as profile
import pstats


prefix = '/opt/ml'
model_path = os.path.join(prefix, 'model')


class ImputationService(object):
    imputer = None 

    @classmethod
    def get_imputer(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if cls.imputer is None:
            imputer = SimpleImputer.load(model_path)
            print(imputer.input_columns)
            imputer.load_hpo_model()
            print(imputer.input_columns)
            imputer.imputer.batch_size = 1
            cls.imputer = imputer
        return cls.imputer

    @classmethod
    def impute(cls, input):
        """For the input, do the predictions and return them.
        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""
        imputer = cls.get_imputer()
        return imputer.predict(input)

    @classmethod
    def impute_top_k(cls, input, k=2):
        imputer = cls.get_imputer()
        # actual Imputer inside SimpleImputer
        return imputer.imputer.predict_proba_top_k(input, top_k=k)

    @classmethod
    def explain_instance(cls, instance):
        imputer = cls.get_imputer()
        return imputer.explain_instance(instance)

    @classmethod
    def request_data_frame(cls, post_body):
        post_body = json.loads(post_body)
        print('label col', cls.get_imputer().output_column)
        instances = []
        for instance in post_body['instances']:
            # feature concat
            tmp_col = ''
            for key in list(instance.keys()):
                tmp_col = tmp_col + ' ' + instance[key]
                del instance[key]
            instance['_concat'] = tmp_col
            instance[cls.get_imputer().output_column] = ''
            instances.append(instance)
        df = pd.DataFrame(instances)
        return df


# The flask app for serving predictions
app = flask.Flask(__name__)


@app.route('/ping', methods=['GET'])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""

    health = ImputationService.get_imputer() is not None

    status = 200 if health else 404
    return flask.Response(response='\n', status=status, mimetype='application/json')


@app.route('/invocations', methods=['POST'])
def transformation():
    """Do an inference on a single batch of data. In this sample server, we take data as CSV, convert
    it to a pandas data frame for internal use and then convert the predictions back to CSV (which really
    just means one prediction per line, since there's a single column.
    """
    data = None

    # Convert from CSV to pandas
    if flask.request.content_type == 'text/csv':
        data = flask.request.data.decode('utf-8')
        s = StringIO(data)
        data = pd.read_csv(s, error_bad_lines=False, quoting=3)
        print('Invoked with {} records'.format(data.shape[0]))
        # Do the prediction
        new_data = ImputationService.impute(data)

        # Convert from numpy back to CSV
        out = StringIO()
        new_data.to_csv(out, header=False, index=False)
        result = out.getvalue()

        return flask.Response(response=result, status=200, mimetype='text/csv')

    elif flask.request.content_type == 'application/json':
        # p = profile.Profile()
        # p.enable()

        data = ImputationService.request_data_frame(flask.request.data.decode('utf-8'))
        predictions = ImputationService.impute_top_k(data)
        label_col = ImputationService.imputer.output_column
        explanations = []
        for idx in range(data.shape[0]):
            expl = ImputationService.explain_instance(data.iloc[idx])
            k = [k for k in expl.keys() if k != 'explained_label'][0]
            expl['tokens'] = expl[k]
            del expl[k]
            # top 3 positive covar tokens and only the token
            expl['tokens'] = [e[0] for e in expl['tokens'] if e[1] > 0][:3]
            explanations.append(expl)

        response = {
            'instances': [
                {
                    'label_column': label_col,
                    'predictions': [{
                        'predicted': label,
                        'predicted_probability': float(proba)
                    } for label, proba in instance_preds],
                    'prediction_explanations': explanations
                } for instance_preds in predictions[label_col]
            ]
        }

        # p.disable()
        # pstats.Stats(p).sort_stats('tottime').print_stats(50)

        return flask.Response(response=json.dumps(response), status=200, mimetype='application/json')
    else:
        return flask.Response(response='This predictor only supports CSV data', status=415, mimetype='text/plain')

