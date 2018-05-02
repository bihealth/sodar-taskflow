import random
import string

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

    # TODO: Remove stuff from user folders
    # TODO: Remove stuff from trash

    # Remove project folders
    try:
        irods.collections.remove(
            PROJECT_ROOT, recurse=True, force=True)

        if verbose:
            print('Removed project root: {}'.format(PROJECT_ROOT))

    except Exception:
        pass    # This is OK, the root just wasn't there

    # Remove created user groups and users
    # NOTE: user_groups.remove does both
    for g in irods.query(UserGroup).all():
        if g[UserGroup.name] not in PERMANENT_USERS:
            irods.user_groups.remove(user_name=g[UserGroup.name])

            if verbose:
                print('Removed user: {}'.format(g[UserGroup.name]))


def get_project_path(project_uuid):
    """Return project path"""
    return '{project_root}/{uuid_prefix}/{uuid}'.format(
        project_root=PROJECT_ROOT,
        uuid_prefix=project_uuid[:2],
        uuid=project_uuid)


def get_landing_zone_root(project_uuid):
    """Return project landing zone root"""
    return '{project_path}/{lz_name}'.format(
        project_path=get_project_path(project_uuid),
        lz_name=settings.TASKFLOW_LANDING_ZONE_DIR)


def get_landing_zone_path(
        project_uuid, user_name, study_dir, assay_dir, zone_title):
    return '{project_path}/{lz_name}/{user_name}/' \
           '{study}/{assay}/{zone_title}'.format(
            project_path=get_project_path(project_uuid),
            lz_name=settings.TASKFLOW_LANDING_ZONE_DIR,
            user_name=user_name,
            study=study_dir,
            assay=assay_dir,
            zone_title=zone_title)


def get_project_group_name(project_uuid):
    """Return project user group name"""
    return 'omics-project-{}'.format(project_uuid)


def get_trash_path(path, add_rand=False):
    """Return base trash path for an object without a versioning suffix. Adds
    random characters if add_rand is set True (for revert operations)"""
    trash_path = '/' + path.split('/')[1] + '/trash/' + '/'.join(
        [x for x in path.split('/')[2:]])

    if add_rand:
        trash_path += '_' + ''.join(
            random.SystemRandom().choice(
                string.ascii_lowercase + string.digits) for x in range(16))

    return trash_path


def get_subcoll_obj_paths(coll):
    """Return paths to all files within collection and its subcollections
    recursively"""
    ret = []

    for sub_coll in coll.subcollections:
        ret += get_subcoll_obj_paths(sub_coll)

    for data_obj in coll.data_objects:
        ret.append(data_obj.path)

    return ret


def get_subcoll_paths(coll):
    """Return paths to all subcollections within collection recursively"""
    ret = []

    for sub_coll in coll.subcollections:
        ret.append(sub_coll.path)
        ret += get_subcoll_paths(sub_coll)

    return ret
