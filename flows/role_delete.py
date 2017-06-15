from .base_flow import BaseLinearFlow
from apis.irods_utils import get_project_group_name
from tasks import omics_tasks, irods_tasks


class Flow(BaseLinearFlow):
    """Flow for removing an user's role in project"""

    def validate(self):
        self.required_fields = [
            'username',
            'user_pk',
            'role_pk']
        return super(Flow, self).validate()

    def build(self, force_fail=False):

        ########
        # Setup
        ########

        existing_group = get_project_group_name(
            self.project_pk)

        ##############
        # iRODS Tasks
        ##############

        self.add_task(
            irods_tasks.RemoveUserFromGroupTask(
                name='Remove user from existing group',
                irods=self.irods,
                inject={
                    'group_name': existing_group,
                    'user_name': self.flow_data['username']}))

        # TODO: TBD: Also e.g. remove landing zone if created?

        ##########################
        # Omics Data Access Tasks
        ##########################

        self.add_task(
            omics_tasks.RemoveRoleTask(
                name='Remove user role',
                omics_api=self.omics_api,
                project_pk=self.project_pk,
                inject={
                    'user_pk': self.flow_data['user_pk'],
                    'role_pk': self.flow_data['role_pk']}))
