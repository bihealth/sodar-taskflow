#!/bin/bash

set -euo pipefail

# Commands:
#
#   wsgi            -- run gunicorn with Django WSGI
#   celeryd         -- run celery worker
#   celerybeat      -- run celerybeat daemon
#
# Environment Variables:
#
#   APP_DIR         -- path to application directory
#                      default: "/usr/src/app"
#   CELERY_QUEUES   -- argument for Celery queues
#                      default: "default,query,import" (all)
#   CELERY_WORKERS  -- celery concurrency/process count
#                      default: "8"
#
#   NO_WAIT         -- skip waiting for servers
#                      default: "0"
#   WAIT_HOSTS      -- hosts to wait for with `wait`
#                      default: "postgres:5432, redis:6379"
#
#   HTTP_HOST       -- host to listen on
#                      default: 0.0.0.0
#   HTTP_PORT       -- port
#                      default: 5005
#   LOG_LEVEL       -- logging verbosity
#                      default: info
#   GUNICORN_TIMEOUT -- timeout for gunicorn workers in seconds
#                       default: 600

APP_DIR=${APP_DIR-/usr/src/app}
CELERY_QUEUES=${CELERY_QUEUES-default,query,import}
CELERY_WORKERS=${CELERY_WORKERS-8}
NO_WAIT=${NO_WAIT-0}
export WAIT_HOSTS=${WAIT_HOSTS-postgres:5432, redis:6379}
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

  >&2 echo "SODAR MIGRATIONS BEGIN"
  python manage.py makemigrations
  python manage.py migrate
  >&2 echo "SODAR MIGRATIONS END"

  exec gunicorn \
    --access-logfile - \
    --log-level "$LOG_LEVEL" \
    --bind "$HTTP_HOST:$HTTP_PORT" \
    --timeout "$GUNICORN_TIMEOUT" \
    config.wsgi
else
  cd $APP_DIR
  exec "$@"
fi

exit $?
