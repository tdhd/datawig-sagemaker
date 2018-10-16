#!/usr/bin/env sh

source $(dirname $0)/common.sh

image=$1

rm -rf ${CURRENT_DIR}/test/sagemaker_fs/model
rm -rf ${CURRENT_DIR}/test/sagemaker_fs/output

mkdir -p ${CURRENT_DIR}/test/sagemaker_fs/model
mkdir -p ${CURRENT_DIR}/test/sagemaker_fs/output

docker run \
    -v ${CURRENT_DIR}/test/sagemaker_fs:/opt/ml \
    --rm ${image} train