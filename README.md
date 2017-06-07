# Omics Taskflow

The Omics Taskflow component executes taskflows on the iRODS and Omics Data Access databases. It also handles project locking and unlocking using tooz and Redis.


## Requirements

* Ubuntu 16.04
* Python 3.5
* Docker and docker-compose
* Redis
* iRODS iCAT server
* [Omics Data Access](https://gitlab.bihealth.org/cubi/omics_data_access)


## Installation

* Set up and activate a `virtualenv` environment for Python 3
* Run `pip install -r requirements.txt`
* Install `docker` and `docker-compose` using apt, if you intend to deploy with Docker
* Set up environment either by running components manually or as Docker containers
    * See below


## Local Execution for Development

* Execute Redis server with `redis-server`
* Start up iRODS iCAT servers with Ansible/Vagrant (**TODO**: Link to project)
    * **NOTE**: You need to have two separate iRODS servers running on different VM hosts:
        * One for development/demonstration
        * One for running omics_taskflow tests
    * Ensure you have the host for the testing irods set up correctly in config/test.py
    * Ensure the env variables used in `config/*.py` files point to correct hosts and ports
* Execute `run_dev.sh` or `run_prod.sh` depending on if you want to run in debug more
* To run unit tests, execute `test.sh`
    * This can also be run against the env running on Docker (see below)


## Local Docker Deployment of Dev Environment

* This will build and run Taskflow along with the required components (Redis and iRODS) on Docker
* On first launch, execute `env_build.sh` to retrieve/build the images
* To bring the env up or down on Docker, execute `env_up.sh` and `env_down.sh`
* If you need to shutdown, rebuild and re-run, execute `env_relaunch.sh`
* **NOTES**
    * This is only usable for short-term development and quick one-time demonstrations 
    * There is no persistent iRODS storage and only one iRODS server
    * Doing both manual testing/demonstration *and* running the automated unit tests on the same iRODS server can (and probably will) yield unwanted results!
    * To sync content to iRODS, run `./manage.py synctaskflow` in Omics Data Access (works for operations implemented at the time of writing)
    * Ensure the `TASKFLOW_OMICS_URL` ENV variable is pointing to where you have the Omics Data Access system running
    * Booting up the iRODS server takes some time (~5-10s on my workstation), so you won't reach it immediately after running the environment.


## Pushing to CUBI GitLab Container Registry

Execute `docker_push.sh` to login, build and push the container image to CUBI GitLab.

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
* Integration with Omics Data Access ongoing
