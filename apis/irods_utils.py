from irods.models import UserGroup
from irods.session import iRODSSession

from config import settings


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT
PERMANENT_USERS = settings.TASKFLOW_TEST_PERMANENT_USERS


def init_irods():
    """Initialize iRODS session. Returns an iRODSSession object."""
    irods = iRODSSession(
        host=settings.TASKFLOW_IRODS_HOST,
        port=settings.TASKFLOW_IRODS_PORT,
        user=settings.TASKFLOW_IRODS_USER,
        password=settings.TASKFLOW_IRODS_PASS,
        zone=settings.TASKFLOW_IRODS_ZONE)

    # Ensure we have a connection
    irods.collections.exists('/{}/home/{}'.format(
        settings.TASKFLOW_IRODS_ZONE, settings.TASKFLOW_IRODS_USER))

    return irods


def cleanup_irods(irods, verbose=True):
    """Cleanup data from iRODS. Used in debugging/testing."""

    # Remove project folders
    irods.collections.remove(
        PROJECT_ROOT, recurse=True)

    if verbose:
        print('Removed project root: {}'.format(PROJECT_ROOT))

    # Remove created user groups and users
    # NOTE: user_groups.remove does both
    for g in irods.query(UserGroup).all():
        if g[UserGroup.name] not in PERMANENT_USERS:
            irods.user_groups.remove(user_name=g[UserGroup.name])

            if verbose:
                print('Removed user: {}'.format(g[UserGroup.name]))


def get_project_path(project_pk):
    """Return project path"""
    return '{}/project{}'.format(
        PROJECT_ROOT, project_pk)


def get_project_group_name(project_pk):
    """Return project user group name"""
    return 'omics-project{}'.format(project_pk)
