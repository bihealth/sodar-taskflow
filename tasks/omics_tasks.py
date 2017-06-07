"""Omics Data Access Django site tasks for Taskflow"""

from .base_task import BaseTask
from apis.omics_api import OmicsRequestException


class OmicsBaseTask(BaseTask):
    """Base Django web UI task"""

    def __init__(
            self, name, project_pk, omics_api, force_fail=False,
            inject=None, *args, **kwargs):
        super(OmicsBaseTask, self).__init__(
            name, force_fail=force_fail, inject=inject, *args, **kwargs)
        self.target = 'omics'
        self.name = '[Omics] {} ({})'.format(name, self.__class__.__name__)
        self.project_pk = project_pk
        self.omics_api = omics_api

    def execute(self, *args, **kwargs):
        # Raise Exception for testing revert()
        # NOTE: This doesn't work if done in pre_execute() or post_execute()
        if self.force_fail:
            raise Exception('force_fail=True')

    def post_execute(self, *args, **kwargs):
        print('{}: {}'.format(
            'force_fail' if self.force_fail else 'Executed',
            self.name))  # DEBUG

    def post_revert(self, *args, **kwargs):
        print('Reverted: {}'.format(self.name))  # DEBUG


class UpdateProjectTask(OmicsBaseTask):
    """Update project title and description"""

    def execute(self, title, description, *args, **kwargs):
        # Get initial data
        self.initial_data = self.omics_api.retrieve(
            'project', self.project_pk).json()

        update_data = {
            'title': title,
            'description': description}

        self.omics_api.update(
            'project', self.project_pk, update_data)

        super(UpdateProjectTask, self).execute(*args, **kwargs)

    def revert(self, title, description, *args, **kwargs):
        if kwargs['result'] is True:
            self.omics_api.update(
                'project', self.project_pk, self.initial_data)


class SetRoleTask(OmicsBaseTask):
    """Update user role in a project"""

    def execute(self, user_pk, role_pk, *args, **kwargs):
        # Get initial data
        query_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk}

        try:
            self.initial_data = self.omics_api.find(
                'role', query_data).json()

        except Exception as ex:
            self.initial_data = None

        set_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk,
            'role_pk': role_pk}
        self.omics_api.set(
            'role', set_data)

        super(SetRoleTask, self).execute(*args, **kwargs)

    def revert(self, user_pk, role_pk, *args, **kwargs):
        if kwargs['result'] is True:
            if self.initial_data:
                self.omics_api.set(
                    'role', self.initial_data)
            else:
                remove_data = {
                    'project_pk': self.project_pk,
                    'user_pk': user_pk}
                self.omics_api.remove('role', remove_data)


class RemoveRoleTask(OmicsBaseTask):
    """Remove user role in a project"""

    def execute(self, user_pk, role_pk, *args, **kwargs):
        # Get initial data
        self.initial_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk,
            'role_pk': role_pk}

        query_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk}

        try:
            self.omics_api.remove('role', query_data).json()
            self.data_modified = True

        except OmicsRequestException:
            pass

        super(RemoveRoleTask, self).execute(*args, **kwargs)

    def revert(self, user_pk, role_pk, *args, **kwargs):
        if kwargs['result'] is True and self.data_modified:
            self.omics_api.set(
                'role', self.initial_data)
