#!/usr/bin/env bash
cd ..
export OMICS_TASKFLOW_SETTINGS=$PWD/config/test.py
python -m unittest discover -v
