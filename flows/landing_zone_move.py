from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path
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
        zone_root = project_path + '/landing_zones'
        user_path = zone_root + '/' + self.flow_data['user_name']
        zone_path = user_path + '/' + self.flow_data['zone_title']

        # TODO: Get collection/file listing from iRODS for iterating

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
                    'status_info': 'Validation in progress, write access '
                                   'disabled'}))    # TODO: Custom info?

        self.add_task(
            irods_tasks.SetAccessTask(
                name='Set user access for landing zone to read only',
                irods=self.irods,
                inject={
                    'access_name': 'read',
                    'path': zone_path,
                    'user_name': self.flow_data['user_name']}))

        # TODO: Delete .done file

        # TODO: Validate MD5 sum for each file

        self.add_task(
            omics_tasks.SetLandingZoneStatusTask(
                name='Set landing zone status to MOVING',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={
                    'zone_pk': self.flow_data['zone_pk'],
                    'status': 'MOVING',
                    'status_info': 'Validation OK, moving files into '
                                   'bio_samples'}))    # TODO: Custom info?

        # TODO: Move files to directories under bio_samples

        # TODO: Set permissions for files (owner, read only for user..)

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
                    'status_info': 'Files moved successfully, landing zone '
                                   'removed'}))  # TODO: Custom info?
