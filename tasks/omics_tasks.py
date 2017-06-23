"""Omics Data Access Django site tasks for Taskflow"""

# TODO: TBD: Proper way to handle reverting the deletion of objects in Django?
# TODO: With simple objects we can recreate them easily, but with e.g. sample
# TODO: sheets it may be difficult. Add some sort of "disabled" tag to soft
# TODO: delete objects instead?


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
        self.initial_data = self.omics_api.send_request(
            'projects/taskflow/project/get',
            {'project_pk': self.project_pk}).json()

        update_data = {
            'project_pk': self.project_pk,
            'title': title,
            'description': description}

        self.omics_api.send_request(
            'projects/taskflow/project/update', update_data)

        super(UpdateProjectTask, self).execute(*args, **kwargs)

    def revert(self, title, description, *args, **kwargs):
        if kwargs['result'] is True:
            self.omics_api.send_request(
                'projects/taskflow/project/update', self.initial_data)


class SetRoleTask(OmicsBaseTask):
    """Update user role in a project"""

    def execute(self, user_pk, role_pk, *args, **kwargs):
        # Get initial data
        query_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk}

        try:
            self.initial_data = self.omics_api.send_request(
                'projects/taskflow/role/get', query_data).json()

        except Exception as ex:
            self.initial_data = None

        set_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk,
            'role_pk': role_pk}
        response = self.omics_api.send_request(
            'projects/taskflow/role/set', set_data)
        self.data_modified = True

        super(SetRoleTask, self).execute(*args, **kwargs)

    def revert(self, user_pk, role_pk, *args, **kwargs):
        if self.data_modified:
            if self.initial_data:
                self.omics_api.send_request(
                    'projects/taskflow/role/set', self.initial_data)
            else:
                remove_data = {
                    'project_pk': self.project_pk,
                    'user_pk': user_pk}
                self.omics_api.send_request(
                    'projects/taskflow/role/delete', remove_data)


class RemoveRoleTask(OmicsBaseTask):
    """Remove user role in a project"""

    def execute(self, user_pk, role_pk, *args, **kwargs):
        # Get initial data
        self.initial_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk,
            'role_pk': role_pk}

        remove_data = {
            'project_pk': self.project_pk,
            'user_pk': user_pk}

        try:
            self.omics_api.send_request(
                'projects/taskflow/role/delete', remove_data)
            self.data_modified = True

        except OmicsRequestException:
            pass

        super(RemoveRoleTask, self).execute(*args, **kwargs)

    def revert(self, user_pk, role_pk, *args, **kwargs):
        if self.data_modified:
            self.omics_api.send_request(
                'projects/taskflow/role/set', self.initial_data)


class SetIrodsDirStatusTask(OmicsBaseTask):
    """Set iRODS dir creation status (True/False) for a sample sheet"""

    def execute(self, dir_status, *args, **kwargs):
        # Get initial data
        query_data = {
            'project_pk': self.project_pk}
        self.initial_data = self.omics_api.send_request(
            'sheets/taskflow/dirstatus/get', query_data).json()

        if self.initial_data['dir_status'] != dir_status:
            set_data = {
                'project_pk': self.project_pk,
                'dir_status': dir_status}
            self.omics_api.send_request(
                'sheets/taskflow/dirstatus/set', set_data)
            self.data_modified = True

        super(SetIrodsDirStatusTask, self).execute(*args, **kwargs)

    def revert(self, dir_status, *args, **kwargs):
        if self.data_modified is True:
            self.omics_api.send_request(
                'sheets/taskflow/dirstatus/set', self.initial_data)


# TODO: Handle revert (see above), before it this must be called last in flow
class RemoveSampleSheetTask(OmicsBaseTask):
    """Remove sample sheet from a project"""

    def execute(self, *args, **kwargs):
        query_data = {
            'project_pk': self.project_pk}

        try:
            self.omics_api.send_request(
                'sheets/taskflow/delete', query_data)
            self.data_modified = True

        except OmicsRequestException:
            pass

        super(RemoveSampleSheetTask, self).execute(*args, **kwargs)

    def revert(self, *args, **kwargs):
        pass    # TODO: How to handle this?


class CreateLandingZoneTask(OmicsBaseTask):
    """Create LandingZone for a project and user in the Omics database"""

    def execute(self, zone_title, user_pk, description, *args, **kwargs):
        create_data = {
            'project_pk': self.project_pk,
            'title': zone_title,
            'user_pk': user_pk,
            'description': description}
        response = self.omics_api.send_request(
            'zones/taskflow/zone/create', create_data)
        self.initial_data = response.json()

        self.data_modified = True
        super(CreateLandingZoneTask, self).execute(*args, **kwargs)

    def revert(self, zone_title, user_pk, description, *args, **kwargs):
        if self.data_modified:
            remove_data = {
                'zone_pk': self.initial_data['zone_pk']}
            self.omics_api.send_request(
                'zones/taskflow/zone/create', remove_data)


# TODO: Handle revert (see above), before it this must be called last in flow
class RemoveLandingZoneTask(OmicsBaseTask):
    """Remove LandingZone from a project and user from the Omics database"""

    def execute(self, zone_pk, *args, **kwargs):
        remove_data = {
           'zone_pk': zone_pk}
        self.omics_api.send_request('zones/taskflow/zone/delete', remove_data)
        self.data_modified = True
        super(RemoveLandingZoneTask, self).execute(*args, **kwargs)

    def revert(self, zone_pk, *args, **kwargs):
        if self.data_modified:
            pass    # TODO: How to handle this?


class SetLandingZoneStatusTask(OmicsBaseTask):
    """Set LandingZone status"""

    def execute(self, zone_pk, status, status_info, *args, **kwargs):
        get_data = {
            'zone_pk': zone_pk}
        self.initial_data = self.omics_api.send_request(
            'zones/taskflow/status/get', get_data).json()

        set_data = {
            'zone_pk': zone_pk,
            'status': status,
            'status_info': status_info}
        self.omics_api.send_request('zones/taskflow/status/set', set_data)

        self.data_modified = True
        super(SetLandingZoneStatusTask, self).execute(*args, **kwargs)

    def revert(self, zone_pk, status, status_info, *args, **kwargs):
        if self.data_modified:
            set_data = {
                'zone_pk': self.initial_data['zone_pk'],
                'status': self.initial_data['status'],
                'status_info': self.initial_data['status_info']}
            self.omics_api.send_request('zones/taskflow/status/set', set_data)
