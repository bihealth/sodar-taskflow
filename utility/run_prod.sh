#!/usr/bin/env bash
cd ..
export OMICS_TASKFLOW_SETTINGS=$PWD/config/production.py
gunicorn omics_taskflow:app
