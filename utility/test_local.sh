#!/usr/bin/env bash
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
export SODAR_TASKFLOW_SETTINGS=${SCRIPT_PATH}/../config/test_local.py
python -m unittest discover -v ${SCRIPT_PATH}/..
