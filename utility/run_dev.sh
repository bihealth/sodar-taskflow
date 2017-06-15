#!/usr/bin/env bash
cd ..
export OMICS_TASKFLOW_SETTINGS=$PWD/config/base.py
python omics_taskflow.py
