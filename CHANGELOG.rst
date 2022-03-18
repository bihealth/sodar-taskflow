SODAR Taskflow Changelog
^^^^^^^^^^^^^^^^^^^^^^^^

Changelog for the SODAR Taskflow service.


Unreleased
==========

Changed
-------

- Upgrade to python-irodsclient v1.1.2 (#93)
- Upgrade general dependencies (#94)
- Drop support for Python <3.8, add support for v3.10 (#95)
- Upgrade to Python v3.8 in Docker build (#95)


v0.6.1 (2022-02-02)
===================

Changed
-------

- Upgrade to python-irodsclient v1.1.0 (#91)
- Allow setting ``DEBUG`` in production config (#92)
- Ignore cache in ``build-docker.sh``


v0.6.0 (2021-12-14)
===================

Added
-----

- ``LABEL`` AND ``MAINTAINER`` in ``Dockerfile`` (#77)
- Replica checksum validation in ``BatchValidateChecksumsTask`` (#78)
- Support for extra data in ``SetLandingZoneStatusTask`` (#81)
- ``status`` and ``flow_name`` arguments for ``RevertLandingZoneFailTask`` (#86)
- ``flow_name`` argument for ``SetLandingZoneStatusTask``
- ``BatchCheckFilesTask`` for checking file and MD5 checksum presence (#63)
- iRODS environment setup via ``TASKFLOW_IRODS_ENV_OVERRIDE`` (#90)

Changed
-------

- Improve iRODS exception logging (#34)
- Upgrade to python-irodsclient v1.0.0 (#79)
- Update docker build for ``ghcr.io``
- Display user name instead of path in ``SetAccessTask`` revert
- Set zone status to ``NOT CREATED`` on ``landing_zone_create`` failure (#86)
- Improve ``RevertLandingZoneFailTask`` info messages
- Improve iRODS task exception messages
- Change test config log level to ``CRITICAL``

Fixed
-----

- Redundant info in ``BatchValidateChecksumsTask`` error logging (#80)
- Errors in ``landing_zone_move`` zone status messages (#82)
- ``landing_zone_create`` script user access task exception not resulting in revert (#85)
- ``_raise_irods_exception()`` helper

Removed
-------

- ``set_script_user_access()`` helper, use ``SetAccessTask`` instead (#85)
- ``IRODS_ENV_PATH`` support (#90)


v0.5.0 (2020-06-07)
===================

Added
-----

- Support for ``TASKFLOW_IRODS_PROJECT_ROOT`` setting (#69)
- ``data_delete`` flow for deleting data (#67)
- Support for ``public_guest_access`` field in project updates (#70)
- ``public_access_update`` for setting public read access to collections (#71)
- GitHub CI using GitHub Actions (#74)

Changed
-------

- Upgrade project requirements(#66, #68, #72)
- Unify collection naming (#58)
- Update Docker setup
- Update test cleanup

Fixed
-----

- ``project_description`` field required in ``project_update`` (#64)
- Disallowed empty values not sanitized in ``SetCollectionMetadataTask`` (#64)
- Invalid env variable ``OMICS_TASKFLOW_SETTINGS`` in GitLab CI (#76)


v0.4.0 (2020-04-28)
===================

Added
-----

- Flow ``role_update_irods_batch`` for updating user roles in iRODS (#60)
- Inherited category owners into iRODS user groups in ``project_create`` (#59)
- Bulk updating of user roles in ``project_update`` (#61)
- iRODS task ``RemoveDataObjectTask``

Changed
-------

- Upgrade project requirements (#54)

Fixed
-----

- Crash with Networkx > v2.2 (#52)
- Logging on Flask v1.1+ (#62)


v0.3.4 (2020-01-06)
===================

Added
-----

- Supply optional iRODS options in environment file (#56)
- ``TASKFLOW_IRODS_ENV_PATH`` settings variable (#56)

Changed
-------

- Refactor Python2-style ``super()`` calls (#53)
- Upgrade to python-irodsclient v0.8.2 (#57)

Fixed
-----

- Crash caused by ``networkx==2.4`` installed by ``taskflow`` (#52)
- Unhandled Tooz connection exception (#46)


v0.3.3 (2019-07-05)
===================

Changed
-------

- Improve ``BatchValidateChecksumsTask`` status messages (#50)

Fixed
-----

- Modified owner not created at iRODS in ``project_update`` (#49)

Removed
-------

- Unused ``ValidateDataObjectChecksumTask``


v0.3.2 (2019-02-25)
===================

Added
-----

- Flake8 and Black configuration and CI checks (#42)

Changed
-------

- Prettify Tooz lock status logging (#33)
- Upgrade Python package requirements (#44)
- Update service to work with Flask v1.0+ (#45)
- Upgrade minimum Python version requirement to 3.6
- Format code with Black (#41)
- Code cleanup and refactoring (#42)

Fixed
-----

- Checksum validation failure on tab-formatted .md5 files (#40)
- Wrong landing zone status info for "validate only" mode (#43)

Removed
-------

- Unnecessary byte encoding in Tooz lock API (#33)


v0.3.1 (2018-12-19)
===================

Added
-----

- Support for additional iRODS test server (sodar_core#67)
- Dotenv configuration (#37)
- Use ``TASKFLOW_SODAR_SECRET`` variable for securing connections (sodar_core#46)

Removed
-------

- Unneeded ``utility/test_local.sh`` script


v0.3.0 (2018-10-26)
===================

Added
-----

- More informative exception message for ``CAT_NAME_EXISTS_AS_DATAOBJ`` in ``BatchMoveDataObjectsTask``

Changed
-------

- Rebrand site as SODAR Taskflow (#36)
- Expect ``sodar_url`` parameter instead of ``omics_url`` for SODAR Core compatibility (#35)

Fixed
-----

- Missing exception ``__str__()`` detection in ``_raise_irods_exception()``


v0.2.1 (2018-08-24)
===================

Added
-----

- Workaround for iRODS ticket issue in the bih_proteomics_smb case (omics_data_mgmt#297)
- Proper exception reporting for AddUserToGroupTask (#4)
- Option for validating only in ``landing_zone_move`` (omics_data_mgmt#333)

Changed
-------

- Modify iRODS exception raising in attempt to catch exception name (#34)

Fixed
-----

- Project lock timeouts in async flows due to initiating coordinator in the wrong process (#32)


v0.2.0 (2018-07-03)
===================

Added
-----

- Async support for landing_zone_delete (omics_data_mgmt#228)
- Option for not requiring lock by setting flow.require_lock to False (omics_data_mgmt#231)
- Support for landing zone configuration

Fixed
-----

- Configuration in ``utility/run_prod.sh``
- Concurrent requests failed in debug mode, now using multiple processes
- Failure in acquiring lock was not correctly reported in async mode (omics_data_mgmt#235)
- Project update failure if readme is empty (omics_data_mgmt#251)

Removed
-------

- Support for omics_tasks.RemoveLandingZoneTask as it's no longer needed (omics_data_mgmt#228)


v0.2.0b (2018-06-05)
====================

Added
-----

- Project settings modification in project creation/update
- Helper functions for building directory paths in ``irods_utils``
- This changelog :)

Changed
-------

- Use UUIDs instead of pk:s when referring to omics_data_mgmt objects (#14)
- Modify SODAR Taskflow API URLs
- Improve SODAR API error reporting
- Upgrade to python-irodsclient 0.7.0 (#10)
- Upgrade taskflow and tooz
- Readme rewritten and converted to rst
- Configure sample and landing zone directory names in settings
- Flow ``sheet_delete``: also delete landing zones
- Refactor ``get_project_path()``
- Update ``landing_zone_create`` for assay specific zones (#15)
- Update ``landing_zone_delete`` (#15)
- Modify ``run_prod.sh`` to run Gunicorn with production settings
- Project user groups are now in form of ``omics_project_{UUID}``
- Add proper logging
- Use gevent in production mode (#26)
- Upgrade to gunicorn==19.8.1

Removed
-------

- Flynn references removed as deploying via Flynn is no longer supported
- Redundant debug printouts (all now going to logger)

Fixed
-----

- Data object read access was left for landing zone user account in sample data (#19)
- Failure in ``landing_zone_move`` raised ``NOT CREATED`` instead of ``FAILED`` (#20)
- Missing ``project_readme`` param in ``UpdateProjectTask`` (#23)
- Creating an empty directory if uploading files in landing zone root (#24)


v0.1-PROTOTYPE (2018-04-13)
===========================

- Tagged to freeze the version used with the original omics_data_access prototype
