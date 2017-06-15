#!/usr/bin/env bash
cd ..
export OMICS_TASKFLOW_SETTINGS=$PWD/config/test_local.py
python -m unittest discover -v
