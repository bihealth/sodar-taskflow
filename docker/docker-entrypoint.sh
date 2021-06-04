#!/bin/bash

set -euo pipefail

# Commands:
#
#   wsgi            -- run SODAR Taskflow with GUnicorn WSGI
#
# Environment Variables:
#
#   APP_DIR         -- path to application directory
#                      default: "/usr/src/app"
#   NO_WAIT         -- skip waiting for servers
#                      default: "0"
#   WAIT_HOSTS      -- hosts to wait for with `wait`
#                      default: "redis:6379"
#   HTTP_HOST       -- host to listen on
#                      default: 0.0.0.0
#   HTTP_PORT       -- port
#                      default: 5005
#   LOG_LEVEL       -- logging verbosity
#                      default: info
#   GUNICORN_TIMEOUT -- timeout for gunicorn workers in seconds
#                       default: 600

APP_DIR=${APP_DIR-/usr/src/app}
NO_WAIT=${NO_WAIT-0}
# export WAIT_HOSTS=${WAIT_HOSTS-redis:6379}
export PYTHONUNBUFFERED=${PYTHONUNBUFFERED-1}
HTTP_HOST=${HTTP_HOST-0.0.0.0}
HTTP_PORT=${HTTP_PORT-5005}
LOG_LEVEL=${LOG_LEVEL-info}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT-600}

if [[ "$NO_WAIT" -ne 1 ]]; then
  /usr/local/bin/wait
fi

if [[ "$1" == wsgi ]]; then
  cd $APP_DIR
  export SODAR_TASKFLOW_SETTINGS=${APP_DIR}/config/production.py
  exec gunicorn \
    --access-logfile - \
    --log-level "$LOG_LEVEL" \
    --bind "$HTTP_HOST:$HTTP_PORT" \
    --timeout "$GUNICORN_TIMEOUT" \
    --workers 4 \
    sodar_taskflow:app
else
  cd $APP_DIR
  exec "$@"
fi

exit $?
