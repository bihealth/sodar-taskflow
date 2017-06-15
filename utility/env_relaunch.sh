#!/usr/bin/env bash
docker-compose down
docker-compose build
./env_up.sh

