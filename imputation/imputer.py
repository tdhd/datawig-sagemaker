import os
import pickle
from io import StringIO

import flask
import pandas as pd
from datawig import SimpleImputer

prefix = '/opt/ml'
model_path = os.path.join(prefix, 'model')

class ImputationService(object):
    imputer = None 

    @classmethod
    def get_imputer(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if cls.imputer == None:
            cls.imputer = SimpleImputer.load(model_path)
        return cls.imputer

    @classmethod
    def impute(cls, input):
        """For the input, do the predictions and return them.
        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""
        imputer = cls.get_imputer()
        imputer.predict(input)

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
    else:
        return flask.Response(response='This predictor only supports CSV data', status=415, mimetype='text/plain')

    print('Invoked with {} records'.format(data.shape[0]))

    # Do the prediction
    ImputationService.impute(data)

    # Convert from numpy back to CSV
    out = StringIO()
    data.to_csv(out, header=False, index=False)
    result = out.getvalue()

    return flask.Response(response=result, status=200, mimetype='text/csv')
