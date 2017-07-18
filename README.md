# Omics Taskflow

The Omics Taskflow component executes taskflows on the iRODS and Omics Data
Access databases. It also handles project locking and unlocking using tooz and
Redis.


## Requirements

* Ubuntu 16.04
* Python 3.5
* Docker
* Redis
* iRODS iCAT server
* (Used by [Omics Data Access](https://gitlab.bihealth.org/cubi/omics_data_access))


## Installation

* Install `docker` with apt-get
* Set up and activate a `virtualenv` environment for Python 3
* Run `pip install -r requirements.txt`
* Set up required components either by:
    * Running components manually, or
    * Deploying [omics_docker_env](https://gitlab.bihealth.org/cubi_data_mgmt/omics_docker_env) (recommended, see project for instructions)


## Local Execution for Development

* **NOTE:** Not recommended for demonstration or quick debugging, use [omics_docker_env](https://gitlab.bihealth.org/cubi_data_mgmt/omics_docker_env) instead
* Execute Redis server with `redis-server`
* Start up iRODS iCAT servers with Ansible/Vagrant
    * Ensure you have the host for the testing irods set up correctly in config/test.py
    * Ensure the env variables used in `config/*.py` files point to correct hosts and ports
* Execute `run_dev.sh` or `run_prod.sh` depending on if you want to run in debug more
* To run unit tests, execute `test.sh`
    * This can also be run against the Docker environment


## Pushing to CUBI GitLab Container Registry

* Login to the BIH gitlab with `docker login gitlab.bihealth.org:4567`
* Execute `docker_push.sh` to login, build and push the container image.


## Deployment in Flynn

* **TODO**


## TODO

* More tasks and flows as use cases need them
    * [Guidelines](https://gitlab.bihealth.org/cubi/omics_data_access/issues/52#note_3609) (to be moved in proper documentation)
* More tests
    * Flows
    * Locking
    * Coverage for tests
    * Sonarqube integration
