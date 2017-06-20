#!/usr/bin/env bash
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
export OMICS_TASKFLOW_SETTINGS=${SCRIPT_PATH}/../config/base.py
python ${SCRIPT_PATH}/../omics_taskflow.py
