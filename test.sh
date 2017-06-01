#!/usr/bin/env bash
export OMICS_TASKFLOW_SETTINGS=$PWD/config/test.py
python -m unittest discover -v
