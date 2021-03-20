# Image name: gcr.io/your-project/composer-dags-sync
FROM gcr.io/google.com/cloudsdktool/cloud-sdk:alpine

RUN apk add --update build-base libffi-dev openssl-dev python3-dev py3-pip

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt