FROM python:3-alpine
MAINTAINER MATHZ <sistemas@mathz.dev>

RUN apk --no-cache add \
        supervisor \
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
        python3-dev \
        libxml2-dev \
        libxslt-dev \
        openjdk8-jre

RUN apk --no-cache add postgresql-dev
COPY requirements.txt ./tmp/
RUN pip install -r /tmp/requirements.txt


COPY ms-api.py /script.py
RUN mkdir /uploads
CMD [ "python", "-u", "/script.py" ]
