import importlib.machinery
import os

settings = importlib.machinery.SourceFileLoader(
    'settings', os.getenv('SODAR_TASKFLOW_SETTINGS', None)).load_module()
