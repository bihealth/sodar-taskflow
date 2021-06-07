SODAR Taskflow
==============

.. image:: https://github.com/bihealth/sodar-taskflow/workflows/build/badge.svg
    :target: https://github.com/bihealth/sodar-taskflow/actions?query=workflow%3Abuild

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

The SODAR Taskflow component executes taskflows on the iRODS and SODAR
databases. It also handles project locking and unlocking using tooz and
Redis.


Requirements
------------

- Linux (Ubuntu 20.04 recommended)
- Python 3.6+
- Redis
- Access to *two* dedicated iRODS iCAT servers (one for running tests)


Installation
------------

- Set up and activate a ``virtualenv`` environment for Python 3
- Execute ``pip install -r requirements.txt``
- Set up required components
    * DEFAULT iRODS iCAT Server
    * TEST iRODS iCAT Server
    * Redis-server
- Execute ``utility/run_dev.sh`` for development/debug mode


Local Development Environment
-----------------------------

The `sodar-docker-env <https://github.com/bihealth/sodar-docker-env>`_
setup runs a redis-server and two iRODS servers as Docker containers. It is the
easiest way to get the required servers running. See the repository for
installation instructions.

Make sure to set up your environment variables with the correct iRODS host, zone
and admin user login data, both for the default and test iRODS servers.
See ``config/base.py`` for the variables and their default values.

The default configuration assumes a local DEFAULT iRODS server, while the TEST
iRODS server and Redis are accessed from ``sodar-docker-env``.

**WARNING:** Never set a production server as the TEST server in your
configuration, as this may result in data loss!


Production Deployment
---------------------

SODAR Taskflow can be deployed together with the main SODAR Server using
`Ansible <https://github.com/bihealth/ansible-role-sodar-server>`_ or
`Docker Compose <https://github.com/bihealth/sodar-docker-compose>`_.

**NOTE:** Due to the ``TASKFLOW_SODAR_SECRET`` variable having to match between
SODAR and SODAR Taskflow, only one SODAR instance may be used with one SODAR
Taskflow instance!
