#!/usr/bin/env sh

set -x
# This script shows how to build the Docker image and push it to ECR to be ready for use
# by SageMaker.

# The argument to this script is the image name. This will be used as the image on the local
# machine and combined with the account and region to form the repository name for ECR.
image=$1

# which official release of datawig to install
datawig_version=0.1.7

if [ "$image" == "" ]
then
    echo "Usage: $0 <image-name>"
    exit 1
fi

chmod +x imputation/train
chmod +x imputation/serve

# Get the account number associated with the current IAM credentials
account=$(aws sts get-caller-identity --query Account --output text)
#account='todo'

if [ $? -ne 0 ]
then
    exit 255
fi


# Get the region defined in the current configuration (default to us-west-2 if none defined)
region=$(aws configure get region)
region=${region:-us-west-2}


fullname="${account}.dkr.ecr.${region}.amazonaws.com/datawig:${datawig_version}"

# If the repository doesn't exist in ECR, create it.

aws ecr describe-repositories --repository-names datawig > /dev/null 2>&1

if [ $? -ne 0 ]
then
    aws ecr create-repository --repository-name datawig > /dev/null
fi

# Get the login command from ECR and execute it directly
$(aws ecr get-login --region ${region} --no-include-email)

# Build the docker image locally with the image name and then push it to ECR
# with the full name.

docker build --build-arg datawig_version=$datawig_version -t ${image} .
docker tag ${image} ${fullname}

docker push ${fullname}
