SODAR Taskflow
==============

The SODAR Taskflow component executes taskflows on the iRODS and SODAR
databases. It also handles project locking and unlocking using tooz and
Redis.


Requirements
------------

- Ubuntu 16.04
- Python 3.5+
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

The `sodar_docker_env <https://cubi-gitlab.bihealth.org/CUBI_Engineering/CUBI_Data_Mgmt/sodar_docker_env>`_
setup runs a redis-server and two iRODS servers as Docker containers. It is the
easiest way to get the required servers running. See the repository for
installation instructions.

**NOTE:** At the time of writing, no permanent storage is supported for the
DEFAULT iRODS server in the Docker environment. If this is needed for
development, it is recommended you set up an iRODS iCAT server locally or on
a VM and only use the TEST server from ``sodar_docker_env``. Otherwise, you can
sync project metadata after reboot or Docker container downtime by executing
your SODAR dev instance with ``run.sh sync``. Naturally, data objects in iRODS
will not be re-created.

Make sure to set up your environment variables with the correct iRODS host, zone
and admin user login data, both for the default and test iRODS servers.
See ``config/base.py`` for the variables and their default values.

The default configuration assumes a local DEFAULT iRODS server, while the TEST
iRODS server and Redis are accessed from ``sodar_docker_env``.

**WARNING:** Never set a production server as the TEST server in your
configuration, as this may result in data loss!


Production Deployment
---------------------

Use the `CUBI Ansible Playbooks <https://cubi-gitlab.bihealth.org/CUBI_Operations/Ansible_Playbooks/>`_
by running the role ``cubi.omics-beta`` with the tag ``sodar_taskflow``.

**NOTE:** Due to the ``TASKFLOW_SODAR_SECRET`` variable having to match between
SODAR and SODAR Taskflow, only one SODAR instance may be used with one SODAR
Taskflow instance!
