#!/usr/bin/env bash
docker-compose up -d
echo "NOTE: Wait for approx 5 seconds for ̌iRODS server to be responsive"
echo "NOTE: If not running tests, remember to first run manage.py synctaskflow in Omics Data Access"