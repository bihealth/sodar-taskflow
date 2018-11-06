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

ENV SODAR_TASKFLOW_SETTINGS /app/config/production.py

EXPOSE 5005

CMD ["gunicorn", "--bind=0.0.0.0:5005", "--workers=4", "sodar_taskflow:app"]
