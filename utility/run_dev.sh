#!/usr/bin/env bash
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
export SODAR_TASKFLOW_SETTINGS=${SCRIPT_PATH}/../config/dev.py
python -u ${SCRIPT_PATH}/../sodar_taskflow.py
