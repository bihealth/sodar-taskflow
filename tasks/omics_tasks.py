"""Omics Data Access Django site tasks for Taskflow"""

# TODO: TBD: Proper way to handle reverting the deletion of objects in Django?
# TODO: With simple objects we can recreate them easily, but with e.g. sample
# TODO: sheets it may be difficult. Add some sort of "disabled" tag to soft
# TODO: delete objects instead?

import json

from .base_task import BaseTask
from apis.omics_api import OmicsRequestException


class OmicsBaseTask(BaseTask):
    """Base Django web UI task"""

    def __init__(
            self, name, project_uuid, omics_api, force_fail=False,
            inject=None, *args, **kwargs):
        super(OmicsBaseTask, self).__init__(
            name, force_fail=force_fail, inject=inject, *args, **kwargs)
        self.target = 'omics'
        self.name = '[Omics] {} ({})'.format(name, self.__class__.__name__)
        self.project_uuid = project_uuid
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
        self.execute_data = self.omics_api.send_request(
            'project/taskflow/get',
            {'project_uuid': self.project_uuid}).json()

        update_data = {
            'project_uuid': self.project_uuid,
            'title': title,
            'description': description}

        self.omics_api.send_request(
            'project/taskflow/update', update_data)

        super(UpdateProjectTask, self).execute(*args, **kwargs)

    def revert(self, title, description, *args, **kwargs):
        if kwargs['result'] is True:
            self.omics_api.send_request(
                'project/taskflow/update', self.execute_data)


class SetProjectSettingsTask(OmicsBaseTask):
    """Set project settings"""

    def execute(self, settings, *args, **kwargs):
        # Get initial data
        self.execute_data = self.omics_api.send_request(
            'project/taskflow/settings/get',
            {'project_uuid': self.project_uuid}).json()

        update_data = {
            'project_uuid': self.project_uuid,
            'settings': json.dumps(settings)}

        self.omics_api.send_request(
            'project/taskflow/settings/set', update_data)

        super(SetProjectSettingsTask, self).execute(*args, **kwargs)

    def revert(self, settings, *args, **kwargs):
        if kwargs['result'] is True:
            self.omics_api.send_request(
                'project/taskflow/settings/set', self.execute_data)


class SetRoleTask(OmicsBaseTask):
    """Update user role in a project"""

    def execute(self, user_uuid, role_pk, *args, **kwargs):
        # Get initial data
        query_data = {
            'project_uuid': self.project_uuid,
            'user_uuid': user_uuid}

        try:
            self.execute_data = self.omics_api.send_request(
                'project/taskflow/role/get', query_data).json()

        except Exception as ex:
            self.execute_data = None

        set_data = {
            'project_uuid': self.project_uuid,
            'user_uuid': user_uuid,
            'role_pk': role_pk}
        response = self.omics_api.send_request(
            'project/taskflow/role/set', set_data)
        self.data_modified = True

        super(SetRoleTask, self).execute(*args, **kwargs)

    def revert(self, user_uuid, role_pk, *args, **kwargs):
        if self.data_modified:
            if self.execute_data:
                self.omics_api.send_request(
                    'project/taskflow/role/set', self.execute_data)
            else:
                remove_data = {
                    'project_uuid': self.project_uuid,
                    'user_uuid': user_uuid}
                self.omics_api.send_request(
                    'project/taskflow/role/delete', remove_data)


class RemoveRoleTask(OmicsBaseTask):
    """Remove user role in a project"""

    def execute(self, user_uuid, role_pk, *args, **kwargs):
        # Get initial data
        self.execute_data = {
            'project_uuid': self.project_uuid,
            'user_uuid': user_uuid,
            'role_pk': role_pk}

        remove_data = {
            'project_uuid': self.project_uuid,
            'user_uuid': user_uuid}

        try:
            self.omics_api.send_request(
                'project/taskflow/role/delete', remove_data)
            self.data_modified = True

        except OmicsRequestException:
            pass

        super(RemoveRoleTask, self).execute(*args, **kwargs)

    def revert(self, user_uuid, role_pk, *args, **kwargs):
        if self.data_modified:
            self.omics_api.send_request(
                'project/taskflow/role/set', self.execute_data)


class SetIrodsDirStatusTask(OmicsBaseTask):
    """Set iRODS dir creation status (True/False) for a sample sheet"""

    def execute(self, dir_status, *args, **kwargs):
        # Get initial data
        query_data = {
            'project_uuid': self.project_uuid}
        self.execute_data = self.omics_api.send_request(
            'samplesheets/taskflow/dirs/get', query_data).json()

        if self.execute_data['dir_status'] != dir_status:
            set_data = {
                'project_uuid': self.project_uuid,
                'dir_status': dir_status}
            self.omics_api.send_request(
                'samplesheets/taskflow/dirs/set', set_data)
            self.data_modified = True

        super(SetIrodsDirStatusTask, self).execute(*args, **kwargs)

    def revert(self, dir_status, *args, **kwargs):
        if self.data_modified is True:
            self.omics_api.send_request(
                'samplesheets/taskflow/dirs/set', self.execute_data)


# TODO: Handle revert (see above), before it this must be called last in flow
class RemoveSampleSheetTask(OmicsBaseTask):
    """Remove sample sheet from a project"""

    def execute(self, *args, **kwargs):
        query_data = {
            'project_uuid': self.project_uuid}

        try:
            self.omics_api.send_request(
                'samplesheets/taskflow/delete', query_data)
            self.data_modified = True

        except OmicsRequestException:
            pass

        super(RemoveSampleSheetTask, self).execute(*args, **kwargs)

    def revert(self, *args, **kwargs):
        pass    # TODO: How to handle this?


class CreateLandingZoneTask(OmicsBaseTask):
    """Create LandingZone for a project and user in the Omics database"""

    def execute(
            self, zone_title, user_uuid, assay_uuid, description,
            *args, **kwargs):
        create_data = {
            'project_uuid': self.project_uuid,
            'assay_uuid': assay_uuid,
            'title': zone_title,
            'user_uuid': user_uuid,
            'description': description}
        response = self.omics_api.send_request(
            'landingzones/taskflow/create', create_data)
        self.execute_data = response.json()

        self.data_modified = True
        super(CreateLandingZoneTask, self).execute(*args, **kwargs)

    def revert(
            self, zone_title, user_uuid, assay_uuid, description,
            *args, **kwargs):
        if self.data_modified:
            remove_data = {
                'zone_uuid': self.execute_data['zone_uuid']}
            self.omics_api.send_request(
                'landingzones/taskflow/create', remove_data)


# TODO: Handle revert (see above), before it this must be called last in flow
class RemoveLandingZoneTask(OmicsBaseTask):
    """Remove LandingZone from a project and user from the Omics database"""

    def execute(self, zone_uuid, *args, **kwargs):
        remove_data = {
           'zone_uuid': zone_uuid}
        self.omics_api.send_request('landingzones/taskflow/delete', remove_data)
        self.data_modified = True
        super(RemoveLandingZoneTask, self).execute(*args, **kwargs)

    def revert(self, zone_uuid, *args, **kwargs):
        if self.data_modified:
            pass    # TODO: How to handle this?


class SetLandingZoneStatusTask(OmicsBaseTask):
    """Set LandingZone status"""

    def execute(
            self, status, status_info, zone_uuid=None, *args, **kwargs):
        set_data = {
            'status': status,
            'status_info': status_info,
            'zone_uuid': zone_uuid}

        self.omics_api.send_request(
            'landingzones/taskflow/status/set', set_data)
        self.data_modified = True
        super(SetLandingZoneStatusTask, self).execute(*args, **kwargs)

    def revert(
            self, status, status_info, zone_uuid=None, *args, **kwargs):
        pass    # Disabled, call RevertLandingZoneStatusTask to revert


class RevertLandingZoneFailTask(OmicsBaseTask):
    """Set LandingZone status in case of failure"""

    def execute(self, zone_uuid, info_prefix, *args, **kwargs):
        super(RevertLandingZoneFailTask, self).execute(*args, **kwargs)

    def revert(self, zone_uuid, info_prefix, *args, **kwargs):
        status_info = info_prefix

        for k, v in kwargs['flow_failures'].items():
            status_info += ': '
            status_info += str(v.exception) if \
                v.exception else 'unknown error'

        set_data = {
            'zone_uuid': zone_uuid,
            'status': 'FAILED',
            'status_info': status_info}
        self.omics_api.send_request(
            'landingzones/taskflow/status/set', set_data)
