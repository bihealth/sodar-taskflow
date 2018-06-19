Omics Taskflow
==============

The Omics Taskflow component executes taskflows on the iRODS and Omics Data
Management databases. It also handles project locking and unlocking using tooz and
Redis.

**TODO:** Update docker instructions after updating omics_docker_env.


Requirements
------------

* Ubuntu 16.04
* Python 3.5+
* Redis
* Access to a dedicated iRODS iCAT server


Installation
------------

* Set up and activate a ``virtualenv`` environment for Python 3
* Run ``pip install -r requirements.txt``
* Set up required components either by:
    * Running components manually, or
    * Deploying omics_docker_env (recommended, see project for instructions)


Local Execution for Development
-------------------------------

The first two steps are already correctly setup if you are using the Docker in ``omics_docker_env``.

* Execute Redis server with ``redis-server``
* Make sure an iRODS iCAT server 4.2+ is started and properly configured
    * The rule file ``omics.re`` must be available and configured in ``/etc/irods/server_config.json`` under ``re_rulebase_set``
    * The value for ``default_hash_scheme`` in ``/etc/irods/server_config.json`` must be ``"MD5"``

The third step is also already setup with ``omics_docker_env``.

* Set up your environment variables with the correct iRODS host, zone and admin user login data
    * See ``config/base.py`` for the variables and their default values

The fourth step is only all that you need to do in development.

* Execute ``utility/run_dev.sh`` or ``utility/run_prod.sh`` depending on if you want to run in debug mode

And finally, to run tests and a caveat lector!

* To run unit tests, execute ``utility/test.sh``
    * **IMPORTANT:** Do **NOT** run tests on a production server or an iRODS server used for any other project, as server data **WILL** be wiped between automated tests!


Pushing to CUBI GitLab Container Registry
-----------------------------------------

**NOTE:** Currently out of date, to be updated

* Login to the BIH gitlab with ``docker login cubi-gitlab.bihealth.org:4567``
* Execute ``docker_push.sh`` to login, build and push the container image.


Server Deployment
-----------------

Use the `CUBI Ansible Playbooks <https://cubi-gitlab.bihealth.org/CUBI_Operations/Ansible_Playbooks/>`_
by running the role ``cubi.omics-beta`` with the tag ``omics_taskflow``.
