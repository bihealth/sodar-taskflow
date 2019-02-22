#!/usr/bin/env bash
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
black ${SCRIPT_PATH}/.. -l 80 --skip-string-normalization --exclude ".git|.venv|env" $1
