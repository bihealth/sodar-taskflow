from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_sample_path, get_landing_zone_path, \
    get_subcoll_obj_paths, get_project_group_name, get_subcoll_paths

from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT
SAMPLE_DIR = settings.TASKFLOW_SAMPLE_DIR


class Flow(BaseLinearFlow):
    """Flow for validating and moving files from a landing zone to the
    sample data collection in iRODS"""

    def validate(self):
        self.supported_modes = [
            'sync',
            'async']
        self.required_fields = [
            'zone_title',
            'zone_uuid',
            'assay_path_zone',
            'assay_path_samples',
            'user_name']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        # Set zone status in the Django site
        set_data = {
            'zone_uuid': self.flow_data['zone_uuid'],
            'status': 'PREPARING',
            'status_info': 'Preparing transaction for validation and moving'}
        self.omics_api.send_request(
            'landingzones/taskflow/status/set', set_data)

        ########
        # Setup
        ########

        project_group = get_project_group_name(self.project_uuid)
        sample_path = get_sample_path(
            project_uuid=self.project_uuid,
            assay_path=self.flow_data['assay_path_samples'])
        zone_path = get_landing_zone_path(
            project_uuid=self.project_uuid,
            user_name=self.flow_data['user_name'],
            assay_path=self.flow_data['assay_path_zone'],
            zone_title=self.flow_data['zone_title'],
            zone_config=self.flow_data['zone_config'])
        admin_name = settings.TASKFLOW_IRODS_USER

        # Get landing zone file paths (without .md5 files) from iRODS
        zone_coll = self.irods.collections.get(zone_path)
        zone_objects = get_subcoll_obj_paths(zone_coll)

        zone_objects_nomd5 = list(set([
            p for p in zone_objects if p[p.rfind('.') + 1:].lower() != 'md5']))

        # Get all collections with root path
        zone_all_colls = [zone_path]
        zone_all_colls += get_subcoll_paths(zone_coll)

        # Get list of collections containing files (ignore empty colls)
        zone_object_colls = list(set([
            p[:p.rfind('/')] for p in zone_objects]))

        # Convert these to collections inside sample dir
        sample_colls = list(set([
            sample_path + '/' + '/'.join(p.split('/')[10:]) for
            p in zone_object_colls if len(p.split('/')) > 10]))

        # print('sample_path: {}'.format(sample_path))                # DEBUG
        # print('zone_objects: {}'.format(zone_objects))              # DEBUG
        # print('zone_objects_nomd5: {}'.format(zone_objects_nomd5))  # DEBUG
        # print('zone_all_colls: {}'.format(zone_all_colls))          # DEBUG
        # print('zone_object_colls: {}'.format(zone_object_colls))    # DEBUG
        # print('sample_colls: {}'.format(sample_colls))              # DEBUG

        ########
        # Tasks
        ########

        # If async, set up task to set landing zone status to failed
        if self.request_mode == 'async':
            self.add_task(
                omics_tasks.RevertLandingZoneFailTask(
                    name='Set landing zone status to FAILED on revert',
                    omics_api=self.omics_api,
                    project_uuid=self.project_uuid,
                    inject={
                        'zone_uuid': self.flow_data['zone_uuid'],
                        'info_prefix': 'Running asynchronous job failed'}))

        self.add_task(
            omics_tasks.SetLandingZoneStatusTask(
                name='Set landing zone status to VALIDATING',
                omics_api=self.omics_api,
                project_uuid=self.project_uuid,
                inject={
                    'zone_uuid': self.flow_data['zone_uuid'],
                    'status': 'VALIDATING',
                    'status_info':
                        'Validating {} files, write access disabled'.format(
                            len(zone_objects_nomd5))}))

        # If "validate_only" is set, return without moving and set status
        if ('validate_only' in self.flow_data and
                self.flow_data['validate_only']):
            self.add_task(
                omics_tasks.SetLandingZoneStatusTask(
                    name='Set landing zone status to ACTIVE',
                    omics_api=self.omics_api,
                    project_uuid=self.project_uuid,
                    inject={
                        'zone_uuid': self.flow_data['zone_uuid'],
                        'status': 'ACTIVE',
                        'status_info':
                            'Successfully validated {} file{}'.format(
                                len(zone_objects_nomd5),
                                's' if len(zone_objects_nomd5) != 1 else '')}))
            return

        # Else continue with moving
        self.add_task(
            irods_tasks.SetInheritanceTask(
                name='Set inheritance for landing zone collection {}'.format(
                    zone_path),
                irods=self.irods,
                inject={
                    'path': zone_path,
                    'inherit': True}))

        self.add_task(
            irods_tasks.SetAccessTask(
                name='Set admin "{}" owner access for zone coll {}'.format(
                    admin_name, zone_path),
                irods=self.irods,
                inject={
                    'access_name': 'own',
                    'path': zone_path,
                    'user_name': admin_name}))

        self.add_task(
            irods_tasks.SetAccessTask(
                name='Set user "{}" read access for zone collection {}'.format(
                    self.flow_data['user_name'], zone_path),
                irods=self.irods,
                inject={
                    'access_name': 'read',
                    'path': zone_path,
                    'user_name': self.flow_data['user_name']}))

        # Workaround for omics_data_mgmt#297
        # If script user is set and exists, set read access
        self.set_script_user_access('read', zone_path)

        self.add_task(
            irods_tasks.BatchValidateChecksumsTask(
                name='Batch validate MD5 checksums of {} data objects'.format(
                    len(zone_objects_nomd5)),
                irods=self.irods,
                inject={
                    'paths': zone_objects_nomd5}))

        self.add_task(
            omics_tasks.SetLandingZoneStatusTask(
                name='Set landing zone status to MOVING',
                omics_api=self.omics_api,
                project_uuid=self.project_uuid,
                inject={
                    'zone_uuid': self.flow_data['zone_uuid'],
                    'status': 'MOVING',
                    'status_info':
                        'Validation OK, moving {} files into {}'.format(
                            len(zone_objects_nomd5), SAMPLE_DIR)}))

        if sample_colls:
            self.add_task(
                irods_tasks.BatchCreateCollectionsTask(
                    name='Create collections in {}'.format(SAMPLE_DIR),
                    irods=self.irods,
                    inject={
                        'paths': sample_colls}))

        self.add_task(
            irods_tasks.BatchMoveDataObjectsTask(
                name='Move {} files and set project group '
                     'read access'.format(len(zone_objects)),
                irods=self.irods,
                inject={
                    'src_root': zone_path,
                    'dest_root': sample_path,
                    'src_paths': zone_objects,
                    'access_name': 'read',
                    'user_name': project_group}))

        self.add_task(
            irods_tasks.SetAccessTask(
                name='Remove user "{}" access from sample collection {}'.format(
                    self.flow_data['user_name'], sample_path),
                irods=self.irods,
                inject={
                    'access_name': 'null',
                    'path': sample_path,
                    'user_name': self.flow_data['user_name']}))

        # Workaround for omics_data_mgmt#297
        # If script user is set and exists, remove access
        self.set_script_user_access('null', sample_path)

        self.add_task(
            irods_tasks.RemoveCollectionTask(
                name='Remove the landing zone collection',
                irods=self.irods,
                inject={
                    'path': zone_path}))

        self.add_task(
            omics_tasks.SetLandingZoneStatusTask(
                name='Set landing zone status to MOVED',
                omics_api=self.omics_api,
                project_uuid=self.project_uuid,
                inject={
                    'zone_uuid': self.flow_data['zone_uuid'],
                    'status': 'MOVED',
                    'status_info':
                        'Successfully moved {} files, landing zone '
                        'removed'.format(len(zone_objects_nomd5))}))
