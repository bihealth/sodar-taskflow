from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path, get_project_group_name
from tasks import omics_tasks, irods_tasks


class Flow(BaseLinearFlow):
    """Flow for updating a project: modifies project metadata and owner"""

    def validate(self):
        self.required_fields = [
            'project_title',
            'project_description',
            'project_readme',
            'owner_uuid',
            'owner_username',
            'owner_role_pk',
            'old_owner_uuid',
            'old_owner_username',
            'settings']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_uuid)
        project_group = get_project_group_name(self.project_uuid)

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

        # Update owner if changed
        if self.flow_data['owner_uuid'] != self.flow_data['old_owner_uuid']:
            self.add_task(
                irods_tasks.RemoveUserFromGroupTask(
                    name='Remove old owner "{}" from project user '
                         'group'.format(self.flow_data['old_owner_username']),
                    irods=self.irods,
                    inject={
                        'group_name': project_group,
                        'user_name': self.flow_data['old_owner_username']}))

            self.add_task(
                irods_tasks.AddUserToGroupTask(
                    name='Add new owner "{}" to project user group'.format(
                        self.flow_data['owner_username']),
                    irods=self.irods,
                    inject={
                        'group_name': project_group,
                        'user_name': self.flow_data['owner_username']}))

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.UpdateProjectTask(
                name='Update project data',
                project_uuid=self.project_uuid,
                omics_api=self.omics_api,
                inject={
                    'title': self.flow_data['project_title'],
                    'description': self.flow_data['project_description'],
                    'readme': self.flow_data['project_readme']}))

        # Update owner if changed
        if self.flow_data['owner_uuid'] != self.flow_data['old_owner_uuid']:
            self.add_task(
                omics_tasks.RemoveRoleTask(
                    name='Remove owner role from user "{}"'.format(
                        self.flow_data['old_owner_username']),
                    omics_api=self.omics_api,
                    project_uuid=self.project_uuid,
                    inject={
                        'user_uuid': self.flow_data['old_owner_uuid'],
                        'role_pk': self.flow_data['owner_role_pk']}))

            self.add_task(
                omics_tasks.SetRoleTask(
                    name='Set owner role for user "{}"'.format(
                        self.flow_data['owner_username']),
                    omics_api=self.omics_api,
                    project_uuid=self.project_uuid,
                    inject={
                        'user_uuid': self.flow_data['owner_uuid'],
                        'role_pk': self.flow_data['owner_role_pk']}))

        self.add_task(
            omics_tasks.SetProjectSettingsTask(
                name='Set project settings',
                omics_api=self.omics_api,
                project_uuid=self.project_uuid,
                inject={
                    'settings': self.flow_data['settings']}))
