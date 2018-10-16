#!/usr/bin/env sh

source $(dirname $0)/common.sh

image=$1

docker run \
    -v ${CURRENT_DIR}/test/sagemaker_fs:/opt/ml \
    -p ${SAGEMAKER_HTTP_PORT}:${SAGEMAKER_HTTP_PORT} \
    --rm ${image} serve
