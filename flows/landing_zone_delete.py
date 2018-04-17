from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path
from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT


class Flow(BaseLinearFlow):
    """Flow for deleting a landing zone from a project and a user in iRODS"""

    def validate(self):
        self.required_fields = [
            'zone_uuid',
            'zone_title',
            'user_name',
            'user_uuid']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_uuid)
        zone_path = project_path + '/landing_zones/' + \
            self.flow_data['user_name'] + '/' + \
            self.flow_data['zone_title']

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.RemoveCollectionTask(
                name='Remove the landing zone collection',
                irods=self.irods,
                inject={
                    'path': zone_path}))

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.RemoveLandingZoneTask(
                name='Remove the landing zone from the Omics database',
                omics_api=self.omics_api,
                project_uuid=self.project_uuid,
                inject={
                    'zone_uuid': self.flow_data['zone_uuid']}))
