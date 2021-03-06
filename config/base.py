import dotenv
import os

dotenv.load_dotenv()

# Flask
DEBUG = True
FLASK_ENV = 'development'
TESTING = False

# Taskflow
TASKFLOW_LOG_LEVEL = 'DEBUG'
TASKFLOW_LOG_MAX_BYTES = os.getenv('TASKFLOW_LOG_MAX_BYTES', 8388608)
TASKFLOW_LOG_TO_FILE = os.getenv('TASKFLOW_LOG_TO_FILE', False)
TASKFLOW_LOG_PATH = os.getenv('TASKFLOW_LOG_PATH', 'sodar_taskflow.log')

TASKFLOW_IRODS_HOST = os.getenv('TASKFLOW_IRODS_HOST', '0.0.0.0')
TASKFLOW_IRODS_PORT = os.getenv('TASKFLOW_IRODS_PORT', 4477)
TASKFLOW_IRODS_ZONE = os.getenv('TASKFLOW_IRODS_ZONE', 'omicsZone')
TASKFLOW_IRODS_USER = os.getenv('TASKFLOW_IRODS_USER', 'rods')
TASKFLOW_IRODS_PASS = os.getenv('TASKFLOW_IRODS_PASS', 'rods')
TASKFLOW_IRODS_ROOT_PATH = os.getenv('TASKFLOW_IRODS_ROOT_PATH', None)
TASKFLOW_ALLOW_IRODS_CLEANUP = os.getenv('TASKFLOW_ALLOW_IRODS_CLEANUP', False)

TASKFLOW_IRODS_ENV = {
    'irods_encryption_algorithm': 'AES-256-CBC',
    'irods_encryption_key_size': 32,
    'irods_encryption_num_hash_rounds': 16,
    'irods_encryption_salt_size': 8,
}
TASKFLOW_IRODS_ENV_OVERRIDE = os.getenv('TASKFLOW_IRODS_ENV_OVERRIDE', None)
TASKFLOW_IRODS_CERT_PATH = os.getenv('TASKFLOW_IRODS_CERT_PATH', None)

# iRODS server test settings
TASKFLOW_IRODS_PROJECT_ROOT = '/{}{}/projects'.format(
    TASKFLOW_IRODS_ZONE,
    ('/' + TASKFLOW_IRODS_ROOT_PATH)
    if TASKFLOW_IRODS_ROOT_PATH and len(TASKFLOW_IRODS_ROOT_PATH) > 0
    else '',
)
TASKFLOW_SAMPLE_COLL = 'sample_data'
TASKFLOW_LANDING_ZONE_COLL = 'landing_zones'

TASKFLOW_SODAR_URL = os.getenv('TASKFLOW_SODAR_URL', 'http://0.0.0.0:8000')
TASKFLOW_REDIS_URL = os.getenv('TASKFLOW_REDIS_URL', 'redis://0.0.0.0:6633')

TASKFLOW_SODAR_SECRET = os.getenv('TASKFLOW_SODAR_SECRET', 'CHANGE ME!')

# iRODS test server settings (default = sodar_docker_env)
# NOTE: Zone remains the same
TASKFLOW_IRODS_TEST_HOST = os.getenv('TASKFLOW_IRODS_TEST_HOST', '0.0.0.0')
TASKFLOW_IRODS_TEST_PORT = os.getenv('TASKFLOW_IRODS_TEST_PORT', 4488)
TASKFLOW_IRODS_TEST_USER = os.getenv('TASKFLOW_IRODS_TEST_USER', 'rods')
TASKFLOW_IRODS_TEST_PASS = os.getenv('TASKFLOW_IRODS_TEST_PASS', 'rods')

TASKFLOW_LOCK_RETRY_COUNT = 2
TASKFLOW_LOCK_RETRY_INTERVAL = 3
TASKFLOW_LOCK_ENABLED = True

TASKFLOW_FORCE_FAIL_STRING = 'force_fail=True'

TASKFLOW_TEST_PERMANENT_USERS = [
    'client_user',
    'rods',
    'rodsadmin',
    'public',
    'bih_proteomics_smb',  # Added for temporary proteomics fix
]
