FROM amazonlinux:2017.09

# Update packages and install Python prerequisites
RUN yum update -y
RUN yum -y install python34 \
    python34-pip

# Install prerequisites for Datawig dependencies 
RUN yum install -y gcc \
    gcc-c++ \
    python34-devel

# Install prerequisites for serving 
RUN yum install -y nginx

# Install container specific packages for serving
RUN /usr/bin/pip-3.4 install flask gevent gunicorn

# Install Datawig
# TODO: speed up installaation of Datawig (pandas)
RUN /usr/bin/pip-3.4 install datawig==0.1.7

# PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly
ENV PYTHONUNBUFFERED=TRUE
# PYTHONDONTWRITEBYTECODE keeps Python from writing the .pyc files 
# which are unnecessary in this case
ENV PYTHONDONTWRITEBYTECODE=TRUE
# Also update PATH so that the train and serve programs are found
# when the container is invoked.
ENV PATH="/opt/program:${PATH}"

COPY imputation /opt/program
WORKDIR /opt/program
