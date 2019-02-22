from config import settings

from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_path, get_project_group_name
from tasks import sodar_tasks, irods_tasks


PROJECT_ROOT = settings.TASKFLOW_IRODS_PROJECT_ROOT
TASKFLOW_SAMPLE_DIR = settings.TASKFLOW_SAMPLE_DIR


class Flow(BaseLinearFlow):
    """Flow for creating a directory structure for a sample sheet in iRODS"""

    def validate(self):
        self.required_fields = ['dirs']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        project_path = get_project_path(self.project_uuid)
        sample_path = project_path + '/' + TASKFLOW_SAMPLE_DIR
        project_group = get_project_group_name(self.project_uuid)

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.CreateCollectionTask(
                name='Create collection for sample sheet samples',
                irods=self.irods,
                inject={'path': sample_path},
            )
        )

        self.add_task(
            irods_tasks.SetInheritanceTask(
                name='Set inheritance for sample sheet collection {}'.format(
                    sample_path
                ),
                irods=self.irods,
                inject={'path': sample_path, 'inherit': True},
            )
        )

        self.add_task(
            irods_tasks.SetAccessTask(
                name='Set project user group read access for sample sheet '
                'collection {}'.format(sample_path),
                irods=self.irods,
                inject={
                    'access_name': 'read',
                    'path': sample_path,
                    'user_name': project_group,
                },
            )
        )

        for d in self.flow_data['dirs']:
            dir_path = sample_path + '/' + d
            self.add_task(
                irods_tasks.CreateCollectionTask(
                    name='Create collection {}'.format(dir_path),
                    irods=self.irods,
                    inject={'path': dir_path},
                )
            )

        ##############
        # SODAR Tasks
        ##############

        self.add_task(
            sodar_tasks.SetIrodsDirStatusTask(
                name='Set iRODS directory structure status to True',
                sodar_api=self.sodar_api,
                project_uuid=self.project_uuid,
                inject={'dir_status': True},
            )
        )
