Omics Taskflow Changelog
^^^^^^^^^^^^^^^^^^^^^^^^

Changelog for the Omics Taskflow service.


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
- Modify Omics Taskflow API URLs
- Improve Omics API error reporting
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
