from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path, get_project_group_name
from tasks import sodar_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT


class Flow(BaseLinearFlow):
    """Flow for creating a new project: creates related directories and user
    groups for access, also assigning membership in owner group to owner"""

    def validate(self):
        self.required_fields = [
            'project_title',
            'parent_uuid',
            'owner_username',
            'owner_uuid',
            'owner_role_pk',
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
            irods_tasks.CreateCollectionTask(
                name='Create omics root collection',
                irods=self.irods,
                inject={'path': PROJECT_ROOT},
            )
        )

        self.add_task(
            irods_tasks.CreateCollectionTask(
                name='Create collection for project',
                irods=self.irods,
                inject={'path': project_path},
            )
        )

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Add title metadata to project',
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
                name='Add description metadata to project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'description',
                    'value': self.flow_data.get('project_description', ''),
                },
            )
        )

        self.add_task(
            irods_tasks.SetCollectionMetadataTask(
                name='Add parent metadata to project',
                irods=self.irods,
                inject={
                    'path': project_path,
                    'name': 'parent_uuid',
                    'value': self.flow_data['parent_uuid'],
                },
            )
        )

        self.add_task(
            irods_tasks.CreateUserGroupTask(
                name='Create project user group',
                irods=self.irods,
                inject={'name': project_group},
            )
        )

        self.add_task(
            irods_tasks.SetAccessTask(
                name='Set project user group access',
                irods=self.irods,
                inject={
                    'access_name': 'read',
                    'path': project_path,
                    'user_name': project_group,
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
                name='Add owner user to project user group',
                irods=self.irods,
                inject={
                    'group_name': project_group,
                    'user_name': self.flow_data['owner_username'],
                },
            )
        )

        # Add inherited owners
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

        ##############
        # SODAR Tasks
        ##############

        self.add_task(
            sodar_tasks.SetRoleTask(
                name='Set owner role to user',
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
