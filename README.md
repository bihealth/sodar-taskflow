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

This assumes you have the Omics Data Access app already deployed in Flynn.

## Omics Taskflow

This assumes you have the Omics Data Access app already deployed in Flynn.

Configure Flynn and Docker CLI if you have not done so already, [see instructions here](https://cubi-gitlab.bihealth.org/CUBI_Operations/Operations_Docs/wikis/Flynn-How-To-Deploy-Docker-Image-As-App)

### Taskflow Setup

Create the app:
```
flynn -c {cluster-name} create --remote "" omics-taskflow
```

Add a redis resource:
```
flynn -c {cluster-name} -a omics-taskflow resource add redis
```

Set the omics-taskflow app flynn env:
```
flynn -c {cluster-name} -a omics-taskflow env set \
TASKFLOW_ALLOW_IRODS_CLEANUP=0 \
TASKFLOW_IRODS_HOST={iRODS host} \
TASKFLOW_IRODS_PORT=1247 \
TASKFLOW_OMICS_URL=http://{omics-app-name}-web.discoverd:8080
TASKFLOW_REDIS_URL={Redis URL}
```

**NOTE:** Only set `TASKFLOW_ALLOW_IRODS_CLEANUP` to `1` if the server is used
for developing/debugging!

Push the image to Flynn:

**NOTE:** Make sure you've first built the latest version locally using `docker_build.sh`.
```
flynn -c {cluster-name} -a omics-taskflow docker push omics_taskflow:latest
```

**NOTE:** This may take some time, even after all layers have been pushed
according to the CLI.

Update the port value in the release config:
```
flynn -c {cluster-name} -a omics-taskflow release show --json > release.json
```
Change `processes > app > ports` from `8080` to `5005`.

Update the release:
```
flynn -c {cluster-name} -a omics-taskflow release update release.json
```

Scale the app to start it:
```
flynn -c {cluster-name} -a omics-taskflow scale app=1
```

Flynn automatically generates an external route for your app. Remove it to
prevent users from accessing the app directly. This can be done e.g. from the
Dashboard under "route". This will not affect the internal `*.discoverd`
routing.

### Omics Setup

Set the **omics app** flynn env as follows:
```
flynn -c {cluster-name} -a {omics-app-name} env set \
TASKFLOW_BACKEND_HOST=http://omics-taskflow-web.discoverd \
TASKFLOW_BACKEND_PORT=5005
```

In the omics env variable `ENABLED_BACKEND_PLUGINS`, add `taskflow` to the list.

Finally, synchronize the taskflow data with the following command:
```
flynn -c omics-testing -a {omics-app-name} run /app/manage.py synctaskflow
```

If this returns OK, the Taskflow backend should now be up and operational.
Existing project data has also been synced with iRODS.

### Updating the App Image

Make sure to rebuild the image locally using `docker_build.sh`.

Then push the new image to Flynn:
```
flynn -c {cluster-name} -a omics-taskflow docker push omics_taskflow:latest
```

**NOTE:** Flynn may prompt you to scale the app, but if you already have it
running this is not required.


## TODO

* More tasks and flows as use cases need them
    * [Guidelines](https://gitlab.bihealth.org/cubi/omics_data_access/issues/52#note_3609) (to be moved in proper documentation)
* More tests
    * Flows
    * Locking
    * Coverage for tests
    * Sonarqube integration
