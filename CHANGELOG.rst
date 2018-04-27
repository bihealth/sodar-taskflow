Omics Taskflow Changelog
^^^^^^^^^^^^^^^^^^^^^^^^

Changelog for the Omics Taskflow service.


Unreleased
==========

Added
-----

- Project settings modification in project creation/update
- Helper functions ``get_landing_zone_root()`` and ``get_landing_zone_path()`` in ``irods_utils``
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

Removed
-------

- Flynn references removed as deploying via Flynn is no longer supported


v0.1-PROTOTYPE (2018-04-13)
===========================

- Tagged to freeze the version used with the original omics_data_access prototype
