# Import code adapted from http://stackoverflow.com/a/6246478
import os
import sys

from omics_taskflow import validate_kwargs
from taskflow import engines
from taskflow.patterns import linear_flow as lf

path = os.path.dirname(os.path.abspath(__file__))

for py in [
        f[:-3] for f in os.listdir(path) if f.endswith('.py') and
        f != '__init__.py']:
    mod = __import__('.'.join([__name__, py]), fromlist=[py])
    classes = [
        getattr(mod, x) for x in dir(mod) if isinstance(getattr(mod, x), type)]

    for cls in classes:
        setattr(sys.modules[__name__], cls.__name__, cls)


def get_flow(name):
    """Return flow implementation or None if not found"""
    try:
        return eval('{}.Flow'.format(name))

    except NameError:
        return None
