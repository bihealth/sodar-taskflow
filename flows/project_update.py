from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path
from tasks import omics_tasks, irods_tasks


class Flow(BaseLinearFlow):
    """Flow for updating a project: modifies project metadata"""

    def validate(self):
        self.required_fields = [
            'project_title',
            'project_description']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_pk)

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Update title metadata in project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'title',
                    'value': self.flow_data['project_title']}))

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Update description metadata in project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'description',
                    'value': self.flow_data['project_description']}))

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.UpdateProjectTask(
                name='Update project data',
                project_pk=self.project_pk,
                omics_api=self.omics_api,
                inject={
                    'title': self.flow_data['project_title'],
                    'description': self.flow_data['project_description']}))
