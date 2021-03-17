from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path, get_project_group_name
from tasks import sodar_tasks, irods_tasks


class Flow(BaseLinearFlow):
    """Flow for updating a project: modifies project metadata and owner"""

    def validate(self):
        self.required_fields = [
            'project_title',
            'parent_uuid',
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
                    'value': self.flow_data.get('project_description', ''),
                },
            )
        )

        # TODO: Set public access according to public_guest_access (#71)

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

        # Add new inherited roles
        for username in set(
            [r['username'] for r in self.flow_data.get('roles_add', [])]
        ):
            self.add_task(
                irods_tasks.CreateUserTask(
                    name='Create user "{}" in irods'.format(username),
                    irods=self.irods,
                    inject={'user_name': username, 'user_type': 'rodsuser'},
                )
            )

        for role_add in self.flow_data.get('roles_add', []):
            project_group = get_project_group_name(role_add['project_uuid'])

            self.add_task(
                irods_tasks.AddUserToGroupTask(
                    name='Add user "{}" to project user group "{}"'.format(
                        role_add['username'], project_group
                    ),
                    irods=self.irods,
                    inject={
                        'group_name': project_group,
                        'user_name': role_add['username'],
                    },
                )
            )

        # Delete old inherited roles
        for role_delete in self.flow_data.get('roles_delete', []):
            project_group = get_project_group_name(role_delete['project_uuid'])

            self.add_task(
                irods_tasks.RemoveUserFromGroupTask(
                    name='Remove user "{}" from project user group "{}"'.format(
                        role_delete['username'], project_group
                    ),
                    irods=self.irods,
                    inject={
                        'group_name': project_group,
                        'user_name': role_delete['username'],
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
                    'description': self.flow_data.get(
                        'project_description', ''
                    ),
                    'parent_uuid': self.flow_data['parent_uuid'],
                    'readme': self.flow_data.get('project_readme', ''),
                    'public_guest_access': self.flow_data.get(
                        'public_guest_access', False
                    ),
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
