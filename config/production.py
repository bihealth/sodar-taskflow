from config.base import *

# Flask
DEBUG = False
FLASK_ENV = 'production'

# Taskflow
TASKFLOW_LOG_TO_FILE = os.getenv('TASKFLOW_LOG_TO_FILE', True)
TASKFLOW_LOG_LEVEL = os.getenv('TASKFLOW_LOG_LEVEL', 'WARNING')
