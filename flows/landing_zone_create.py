from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path
from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT


class Flow(BaseLinearFlow):
    """Flow for creating a landing zone for a project and a user in iRODS"""

    def validate(self):
        self.required_fields = [
            'zone_title',
            'user_name',
            'user_pk',
            'dirs']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_pk)
        zone_root = project_path + '/landing_zones'
        user_path = zone_root + '/' + self.flow_data['user_name']
        zone_path = user_path + '/' + self.flow_data['zone_title']

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.CreateCollectionTask(
                name='Create collection for project landing zones',
                irods=self.irods,
                inject={
                    'path': zone_root}))

        self.add_task(
            irods_tasks.CreateUserTask(
                name='Create user if it does not exist',
                irods=self.irods,
                inject={
                    'user_name': self.flow_data['user_name'],
                    'user_type': 'rodsuser'}))

        self.add_task(
            irods_tasks.CreateCollectionTask(
                name='Create collection for user landing zones in project',
                irods=self.irods,
                inject={
                    'path': user_path}))

        self.add_task(
            irods_tasks.CreateCollectionTask(
                name='Create collection for landing zone',
                irods=self.irods,
                inject={
                    'path': zone_path}))

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
                name='Set user owner access for landing zone',
                irods=self.irods,
                inject={
                    'access_name': 'own',
                    'path': zone_path,
                    'user_name': self.flow_data['user_name']}))

        if ('description' in self.flow_data and
                self.flow_data['description'] != ''):
            self.add_task(
                irods_tasks.SetCollectionMetadataTask(
                    name='Add description metadata to landing zone collection',
                    irods=self.irods,
                    inject={
                        'path': zone_path,
                        'name': 'description',
                        'value': self.flow_data['description']}))

        for d in self.flow_data['dirs']:
            dir_path = zone_path + '/' + d
            self.add_task(
                irods_tasks.CreateCollectionTask(
                    name='Create collection {}'.format(dir_path),
                    irods=self.irods,
                    inject={
                        'path': dir_path}))

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.CreateLandingZoneTask(
                name='Create landing zone in the Omics database',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={
                    'zone_title': self.flow_data['zone_title'],
                    'user_pk': self.flow_data['user_pk'],
                    'description': self.flow_data['description']}))
