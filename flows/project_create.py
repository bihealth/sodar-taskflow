from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path,\
    get_project_group_name
from tasks import omics_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT


class Flow(BaseLinearFlow):
    """Flow for creating a new project: creates related directories and user
    groups for access, also assigning membership in owner group to owner"""

    def validate(self):
        self.required_fields = [
            'project_title',
            'project_description',
            'parent_pk',
            'owner_username',
            'owner_pk',
            'owner_role_pk']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_pk)
        project_group = get_project_group_name(self.project_pk)

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.CreateCollectionTask(
                name='Create omics root collection',
                irods=self.irods,
                inject={
                    'path': PROJECT_ROOT}))

        self.add_task(
            irods_tasks.CreateCollectionTask(
                name='Create collection for project',
                irods=self.irods,
                inject={
                    'path': project_path}))

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Add title metadata to project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'title',
                    'value': self.flow_data['project_title']}))

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Add description metadata to project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'description',
                    'value': self.flow_data['project_description']}))

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Add parent metadata to project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'parent_pk',
                    'value': self.flow_data['parent_pk']}))

        self.add_task(
            irods_tasks.CreateUserGroupTask(
                name='Create project user group',
                irods=self.irods,
                inject={
                    'name': project_group}))

        self.add_task(
            irods_tasks.SetAccessTask(
                name='Set project user group access',
                irods=self.irods,
                inject={
                    'access_name': 'read',
                    'path': project_path,
                    'user_name': project_group}))

        self.add_task(
            irods_tasks.CreateUserTask(
                name='Create user for project owner',
                irods=self.irods,
                inject={
                    'user_name': self.flow_data['owner_username'],
                    'user_type': 'rodsuser'}))

        self.add_task(
            irods_tasks.AddUserToGroupTask(
                name='Add owner user to project user group',
                irods=self.irods,
                inject={
                    'group_name': project_group,
                    'user_name': self.flow_data['owner_username']}))

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.SetRoleTask(
                name='Set owner role to user',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={
                    'user_pk': self.flow_data['owner_pk'],
                    'role_pk': self.flow_data['owner_role_pk']}))
