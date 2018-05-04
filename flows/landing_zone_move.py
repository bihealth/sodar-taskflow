from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path, get_sample_path, \
    get_landing_zone_root, get_landing_zone_path, get_subcoll_obj_paths, \
    get_project_group_name, get_subcoll_paths

from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT
SAMPLE_DIR = settings.TASKFLOW_SAMPLE_DIR


# TODO: Modify to move files to correct locations under study/assay!
# TODO: (Old impl. works but creates new dirs directly under sample dir)


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
            'study_dir',
            'assay_dir',
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

        # project_path = get_project_path(self.project_uuid)
        project_group = get_project_group_name(self.project_uuid)
        sample_path = get_sample_path(self.project_uuid)
        # zone_root = get_landing_zone_root(self.project_uuid)
        # user_path = zone_root + '/' + self.flow_data['user_name']
        zone_path = get_landing_zone_path(
            project_uuid=self.project_uuid,
            user_name=self.flow_data['user_name'],
            study_dir=self.flow_data['study_dir'],
            assay_dir=self.flow_data['assay_dir'],
            zone_title=self.flow_data['zone_title'])
        zone_depth = len(zone_path.split('/'))
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
            sample_path + '/' + '/'.join(p.split('/')[zone_depth:]) for
            p in zone_object_colls]))

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
                            SAMPLE_DIR, len(zone_objects_nomd5))}))

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
