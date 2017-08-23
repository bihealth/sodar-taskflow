from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path, get_subcoll_obj_paths,\
    get_project_group_name, get_subcoll_paths
from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT


class Flow(BaseLinearFlow):
    """Flow for validating and moving files from a landing zone to the
    bio_samples collection in iRODS"""

    # NOTE: Prototype implementation, will be done differently in final system

    def validate(self):
        self.required_fields = [
            'zone_title',
            'zone_pk',
            'user_name']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_pk)
        project_group = get_project_group_name(self.project_pk)
        sample_path = project_path + '/bio_samples'
        zone_root = project_path + '/landing_zones'
        user_path = zone_root + '/' + self.flow_data['user_name']
        zone_path = user_path + '/' + self.flow_data['zone_title']
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

        # Convert these to collections inside bio_samples
        sample_colls = list(set([
            sample_path + '/' + '/'.join(p.split('/')[7:]) for
            p in zone_object_colls]))

        # print('zone_objects: {}'.format(zone_objects))              # DEBUG
        # print('zone_objects_nomd5: {}'.format(zone_objects_nomd5))  # DEBUG
        # print('zone_all_colls: {}'.format(zone_all_colls))          # DEBUG
        # print('zone_object_colls: {}'.format(zone_object_colls))    # DEBUG
        # print('sample_colls: {}'.format(sample_colls))              # DEBUG

        ########
        # Tasks
        ########

        self.add_task(
            omics_tasks.SetLandingZoneStatusTask(
                name='Set landing zone status to VALIDATING',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={
                    'zone_pk': self.flow_data['zone_pk'],
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
                name='Set user "{}" owner access for zone collection {}'.format(
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
                    'access_name': 'own',
                    'path': zone_path,
                    'user_name': self.flow_data['user_name']}))

        # TODO: Delete .done file (once we use it)

        for obj_path in zone_objects_nomd5:
            self.add_task(
                irods_tasks.ValidateDataObjectChecksumTask(
                    name='Validate MD5 checksum of "{}"'.format(obj_path),
                    irods=self.irods,
                    inject={
                        'path': obj_path}))

        self.add_task(
            omics_tasks.SetLandingZoneStatusTask(
                name='Set landing zone status to MOVING',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={
                    'zone_pk': self.flow_data['zone_pk'],
                    'status': 'MOVING',
                    'status_info':
                        'Validation OK, moving {} files into '
                        'bio_samples'.format(len(zone_objects_nomd5))}))

        for coll_path in sample_colls:
            self.add_task(
                irods_tasks.CreateCollectionTask(
                    name='Create collection "{}"'.format(coll_path),
                    irods=self.irods,
                    inject={
                        'path': coll_path}))

            self.add_task(
                irods_tasks.SetAccessTask(
                    name='Set group read access for collection "{}"'.format(
                        coll_path),
                    irods=self.irods,
                    inject={
                        'access_name': 'read',
                        'path': coll_path,
                        'user_name': project_group}))

        for obj_path in zone_objects:
            dest_path = sample_path + '/' + '/'.join(obj_path.split('/')[7:-1])
            dest_obj = dest_path + '/' + obj_path.split('/')[-1]

            self.add_task(
                irods_tasks.MoveDataObjectTask(
                    name='Move file "{}"'.format(obj_path),
                    irods=self.irods,
                    inject={
                        'src_path': obj_path,
                        'dest_path': dest_path}))

            # TODO: Could remove this by making bio_samples inheritance=True
            self.add_task(
                irods_tasks.SetAccessTask(
                    name='Set group read access for object "{}"'.format(
                        dest_obj),
                    irods=self.irods,
                    inject={
                        'access_name': 'read',
                        'path': dest_obj,
                        'user_name': project_group,
                        'obj_target': True}))

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
                project_pk=self.project_pk,
                inject={
                    'zone_pk': self.flow_data['zone_pk'],
                    'status': 'MOVED',
                    'status_info':
                        'Successfully moved {} files, landing zone '
                        'removed'.format(len(zone_objects_nomd5))}))
