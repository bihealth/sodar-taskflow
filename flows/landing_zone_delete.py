from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path
from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT


class Flow(BaseLinearFlow):
    """Flow for deleting a landing zone from a project and a user in iRODS"""

    def validate(self):
        self.required_fields = [
            'zone_title',
            'user_name',
            'user_pk']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_pk)
        zone_path = project_path + '/landing_zones/' + \
            self.flow_data['user_name'] + '/' + \
            self.flow_data['zone_title']

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.RemoveCollectionTask(
                name='Remove landing zone collection',
                irods=self.irods,
                inject={
                    'path': zone_path}))

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.RemoveLandingZoneTask(
                name='Remove landing zone from the Omics database',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={
                    'zone_title': self.flow_data['zone_title'],
                    'user_pk': self.flow_data['user_pk']}))
