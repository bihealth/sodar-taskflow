from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path, get_project_group_name
from tasks import sodar_tasks, irods_tasks


class Flow(BaseLinearFlow):
    """Flow for updating a project: modifies project metadata and owner"""

    def validate(self):
        self.required_fields = [
            'project_title',
            'project_description',
            'owner_uuid',
            'owner_username',
            'owner_role_pk',
            'old_owner_uuid',
            'old_owner_username',
            'settings',
        ]
        return super().validate()

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
                    'value': self.flow_data['project_title'],
                },
            )
        )

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Update description metadata in project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'description',
                    'value': self.flow_data['project_description'],
                },
            )
        )

        # Update owner if changed
        if self.flow_data['owner_uuid'] != self.flow_data['old_owner_uuid']:
            self.add_task(
                irods_tasks.RemoveUserFromGroupTask(
                    name='Remove old owner "{}" from project user '
                    'group'.format(self.flow_data['old_owner_username']),
                    irods=self.irods,
                    inject={
                        'group_name': project_group,
                        'user_name': self.flow_data['old_owner_username'],
                    },
                )
            )

            self.add_task(
                irods_tasks.CreateUserTask(
                    name='Create user for project owner',
                    irods=self.irods,
                    inject={
                        'user_name': self.flow_data['owner_username'],
                        'user_type': 'rodsuser',
                    },
                )
            )

            self.add_task(
                irods_tasks.AddUserToGroupTask(
                    name='Add new owner "{}" to project user group'.format(
                        self.flow_data['owner_username']
                    ),
                    irods=self.irods,
                    inject={
                        'group_name': project_group,
                        'user_name': self.flow_data['owner_username'],
                    },
                )
            )

        ##############
        # SODAR Tasks
        ##############

        self.add_task(
            sodar_tasks.UpdateProjectTask(
                name='Update project data',
                project_uuid=self.project_uuid,
                sodar_api=self.sodar_api,
                inject={
                    'title': self.flow_data['project_title'],
                    'description': self.flow_data['project_description'],
                    'readme': self.flow_data['project_readme']
                    if 'project_readme' in self.flow_data
                    else '',
                },
            )
        )

        # Update owner if changed
        if self.flow_data['owner_uuid'] != self.flow_data['old_owner_uuid']:
            self.add_task(
                sodar_tasks.RemoveRoleTask(
                    name='Remove owner role from user "{}"'.format(
                        self.flow_data['old_owner_username']
                    ),
                    sodar_api=self.sodar_api,
                    project_uuid=self.project_uuid,
                    inject={
                        'user_uuid': self.flow_data['old_owner_uuid'],
                        'role_pk': self.flow_data['owner_role_pk'],
                    },
                )
            )

            self.add_task(
                sodar_tasks.SetRoleTask(
                    name='Set owner role for user "{}"'.format(
                        self.flow_data['owner_username']
                    ),
                    sodar_api=self.sodar_api,
                    project_uuid=self.project_uuid,
                    inject={
                        'user_uuid': self.flow_data['owner_uuid'],
                        'role_pk': self.flow_data['owner_role_pk'],
                    },
                )
            )

        self.add_task(
            sodar_tasks.SetProjectSettingsTask(
                name='Set project settings',
                sodar_api=self.sodar_api,
                project_uuid=self.project_uuid,
                inject={'settings': self.flow_data['settings']},
            )
        )
