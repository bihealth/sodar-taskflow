FROM ubuntu:16.04

RUN apt-get update -y && \
    apt-get install -y \
        python3-pip \
        python3-dev \
        git

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app

ENV OMICS_TASKFLOW_SETTINGS /app/config/production.py

CMD ["gunicorn", "--bind=0.0.0.0:5005", "--workers=8", "omics_taskflow:app"]
