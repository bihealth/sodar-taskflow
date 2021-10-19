import json
import logging
import random
import string

from irods.models import UserGroup
from irods.session import iRODSSession

from config import settings


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT
PERMANENT_USERS = settings.TASKFLOW_TEST_PERMANENT_USERS


logger = logging.getLogger('sodar_taskflow')


def init_irods(test_mode=False):
    """Initialize iRODS session, return an iRODSSession object"""

    # iRODS environment
    irods_env = dict(settings.TASKFLOW_IRODS_ENV)
    irods_override = settings.TASKFLOW_IRODS_ENV_OVERRIDE
    if irods_override:
        irods_env.update(
            {
                v[0]: v[1]
                for v in [v.split('=') for v in irods_override.split(',')]
            }
        )
    cert_path = settings.TASKFLOW_IRODS_CERT_PATH
    if cert_path:
        irods_env.update({'irods_ssl_ca_certificate_file': cert_path})
    logger.debug('iRODS env: {}'.format(irods_env))

    # Default server
    if not test_mode:
        irods_kwargs = {
            'host': settings.TASKFLOW_IRODS_HOST,
            'port': settings.TASKFLOW_IRODS_PORT,
            'user': settings.TASKFLOW_IRODS_USER,
            'password': settings.TASKFLOW_IRODS_PASS,
            'zone': settings.TASKFLOW_IRODS_ZONE,
        }
    else:
        irods_kwargs = {
            'host': settings.TASKFLOW_IRODS_TEST_HOST,
            'port': settings.TASKFLOW_IRODS_TEST_PORT,
            'user': settings.TASKFLOW_IRODS_TEST_USER,
            'password': settings.TASKFLOW_IRODS_TEST_PASS,
            'zone': settings.TASKFLOW_IRODS_ZONE,
        }

    irods_kwargs.update(irods_env)
    irods = iRODSSession(**irods_kwargs)

    # Ensure we have a connection
    irods.collections.exists('/{}/home/{}'.format(irods.zone, irods.username))

    logger.debug(
        'Connected to {} server on {}:{}'.format(
            'TEST' if test_mode else 'DEFAULT', irods.host, irods.port
        )
    )

    return irods


def close_irods(irods):
    """Gracefully close iRODS connection if opened"""
    if irods:
        irods.cleanup()


def cleanup_irods_data(irods, verbose=True):
    """Cleanup data from iRODS. Used in debugging/testing."""
    # TODO: Remove stuff from user folders
    # TODO: Remove stuff from trash
    # Remove project folders
    try:
        irods.collections.remove(PROJECT_ROOT, recurse=True, force=True)
        if verbose:
            logger.info('Removed project root: {}'.format(PROJECT_ROOT))
    except Exception:
        pass  # This is OK, the root just wasn't there

    # Remove created user groups and users
    # NOTE: user_groups.remove does both
    for g in irods.query(UserGroup).all():
        if g[UserGroup.name] not in PERMANENT_USERS:
            irods.user_groups.remove(user_name=g[UserGroup.name])
            if verbose:
                logger.info('Removed user: {}'.format(g[UserGroup.name]))


def get_project_path(project_uuid):
    """Return project path"""
    return '{project_root}/{uuid_prefix}/{uuid}'.format(
        project_root=PROJECT_ROOT,
        uuid_prefix=project_uuid[:2],
        uuid=project_uuid,
    )


def get_sample_path(project_uuid, assay_path=None):
    """Return project sample data path"""
    ret = '{project_path}/{sample_dir}'.format(
        project_path=get_project_path(project_uuid),
        sample_dir=settings.TASKFLOW_SAMPLE_COLL,
    )

    if assay_path:
        ret += '/' + assay_path

    return ret


def get_landing_zone_root(project_uuid):
    """Return project landing zone root"""
    return '{project_path}/{lz_dir}'.format(
        project_path=get_project_path(project_uuid),
        lz_dir=settings.TASKFLOW_LANDING_ZONE_COLL,
    )


def get_landing_zone_path(
    project_uuid, user_name, assay_path, zone_title, zone_config
):
    return (
        '{project_path}/{lz_dir}/{user_name}/'
        '{assay}/{zone_title}{zone_config}'.format(
            project_path=get_project_path(project_uuid),
            lz_dir=settings.TASKFLOW_LANDING_ZONE_COLL,
            user_name=user_name,
            assay=assay_path,
            zone_title=zone_title,
            zone_config=('_' + zone_config) if zone_config else '',
        )
    )


def get_project_group_name(project_uuid):
    """Return project user group name"""
    return 'omics_project_{}'.format(project_uuid)


def get_trash_path(path, add_rand=False):
    """Return base trash path for an object without a versioning suffix. Adds
    random characters if add_rand is set True (for revert operations)"""
    trash_path = (
        '/'
        + path.split('/')[1]
        + '/trash/'
        + '/'.join([x for x in path.split('/')[2:]])
    )

    if add_rand:
        trash_path += '_' + ''.join(
            random.SystemRandom().choice(string.ascii_lowercase + string.digits)
            for x in range(16)
        )

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
