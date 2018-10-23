#!/usr/bin/env bash
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
export SODAR_TASKFLOW_SETTINGS=${SCRIPT_PATH}/../config/production.py
gunicorn sodar_taskflow:app --bind 0.0.0.0:5005 --workers 8 --worker-connections 1000 --pythonpath ${SCRIPT_PATH}/..
