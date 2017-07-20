import os

# Flask
DEBUG = True
TESTING = False

# Taskflow
TASKFLOW_IRODS_HOST = os.getenv('TASKFLOW_IRODS_HOST', '0.0.0.0')
TASKFLOW_IRODS_PORT = 1247
TASKFLOW_IRODS_ZONE = 'omicsZone'
TASKFLOW_IRODS_USER = 'rods'
TASKFLOW_IRODS_PASS = 'rods'
TASKFLOW_IRODS_PROJECT_ROOT = '/{}/projects'.format(TASKFLOW_IRODS_ZONE)
TASKFLOW_ALLOW_IRODS_CLEANUP = os.getenv('TASKFLOW_ALLOW_IRODS_CLEANUP', False)

TASKFLOW_OMICS_URL = os.getenv('TASKFLOW_OMICS_URL', 'http://0.0.0.0:8000')
TASKFLOW_REDIS_HOST = os.getenv('TASKFLOW_REDIS_HOST', '0.0.0.0')
TASKFLOW_REDIS_PORT = os.getenv('TASKFLOW_REDIS_PORT', 6379)

TASKFLOW_LOCK_RETRY_COUNT = 5
TASKFLOW_LOCK_RETRY_INTERVAL = 3
TASKFLOW_LOCK_ENABLED = True

TASKFLOW_FORCE_FAIL_STRING = 'force_fail=True'

TASKFLOW_TEST_PERMANENT_USERS = [
    'client_user',
    'rods',
    'rodsadmin',
    'public']
