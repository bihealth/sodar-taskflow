import importlib.machinery
import os

settings = importlib.machinery.SourceFileLoader(
        'settings', os.getenv('OMICS_TASKFLOW_SETTINGS', None)).load_module()
