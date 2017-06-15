from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path,\
    get_project_group_name
from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT


class Flow(BaseLinearFlow):
    """Flow for deleting the project sample sheet in iRODS"""

    def validate(self):
        self.required_fields = []
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_pk)
        sample_path = project_path + '/bio_samples'

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.RemoveCollectionTask(
                name='Remove sample sheet collection',
                irods=self.irods,
                inject={
                    'path': sample_path}))

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.RemoveSampleSheetTask(
                name='Remove sample sheet',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={}))
