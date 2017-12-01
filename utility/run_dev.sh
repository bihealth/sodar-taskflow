#!/usr/bin/env bash
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
export OMICS_TASKFLOW_SETTINGS=${SCRIPT_PATH}/../config/dev.py
python -u ${SCRIPT_PATH}/../omics_taskflow.py | tee ${SCRIPT_PATH}/../taskflow.log
