#!/usr/bin/env sh

source $(dirname $0)/common.sh

set -e 

payload=$1

#ping first 
curl -v http://localhost:${SAGEMAKER_HTTP_PORT}/ping

#impute values
curl --data-binary @${payload} -H "Content-Type:text/csv" -v http://localhost:${SAGEMAKER_HTTP_PORT}/invocations
