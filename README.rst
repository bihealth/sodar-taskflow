Omics Taskflow
==============

The Omics Taskflow component executes taskflows on the iRODS and Omics Data
Management databases. It also handles project locking and unlocking using tooz and
Redis.

:License: MIT


Requirements
------------

* Ubuntu 16.04
* Python 3.5+
* Redis
* Access to an iRODS iCAT server
* Docker (optional)


Installation
------------

* Install ``docker`` with apt-get
* Set up and activate a ``virtualenv`` environment for Python 3
* Run ``pip install -r requirements.txt``
* Set up required components either by:
    * Running components manually, or
    * Deploying omics_docker_env (recommended, see project for instructions)


Local Execution for Development
-------------------------------

* **NOTE:** For offline demonstration or quick debugging, use omics_docker_env instead
* Execute Redis server with ``redis-server``
* Start up iRODS iCAT server, e.g. with Ansible/Vagrant
    * Ensure you have the host for the testing irods set up correctly in config/test.py
    * Ensure the env variables used in ``config/*.py`` files point to correct hosts and ports
* Execute ``run_dev.sh`` or ``run_prod.sh`` depending on if you want to run in debug more
* To run unit tests, execute ``test.sh``
    * This can also be run against the Docker environment


Pushing to CUBI GitLab Container Registry
-----------------------------------------

* Login to the BIH gitlab with ``docker login cubi-gitlab.bihealth.org:4567``
* Execute ``docker_push.sh`` to login, build and push the container image.


Server Deployment
-----------------

**TODO**: Update (Flynn no longer supported)
