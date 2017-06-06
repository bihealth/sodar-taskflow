#!/usr/bin/env bash
export OMICS_TASKFLOW_SETTINGS=$PWD/config/test_local.py
python -m unittest discover -v
