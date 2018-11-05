SODAR Taskflow Changelog
^^^^^^^^^^^^^^^^^^^^^^^^

Changelog for the SODAR Taskflow service.


Unreleased
==========

Added
-----

- Support for additional iRODS test server (sodar_core#67)

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
