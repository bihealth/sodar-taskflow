"""iRODS tasks for Taskflow"""

import random
import string

from irods.access import iRODSAccess
from irods.exception import CollectionDoesNotExist, UserDoesNotExist,\
    UserGroupDoesNotExist, NoResultFound
from irods.models import Collection

from .base_task import BaseTask
from apis.irods_utils import get_trash_path


# NOTE: Yes, we really need this for the python irods client
# TODO: Come up with a more elegant solution..
ACCESS_CONVERSION = {
    'read': 'read object',
    'read object': 'read',
    'write': 'modify object',
    'modify object': 'write',
    'null': 'null'}


class IrodsBaseTask(BaseTask):
    """Base iRODS task"""

    def __init__(self, name, force_fail=False, inject=None, *args, **kwargs):
        super(IrodsBaseTask, self).__init__(
            name, force_fail=force_fail, inject=inject, *args, **kwargs)
        self.target = 'irods'
        self.name = '[iRODS] {} ({})'.format(name, self.__class__.__name__)
        self.irods = kwargs['irods']

    # For when taskflow won't catch a proper exception from the client
    def _raise_irods_execption(self, ex):
        desc = '{} failed: {}'.format(
            self.__class__.__name__, ex.__class__.__name__)

        if str(ex) != '':
            desc += ' ({})'.format(ex)

        print(desc)     # DEBUG
        raise Exception(desc)


class CreateCollectionTask(IrodsBaseTask):
    """Create collection and its parent collections if they doesn't exist
    (imkdir)"""

    def execute(self, path, *args, **kwargs):
        # Create parent collections if they don't exist
        self.execute_data['created_colls'] = []

        for i in range(2, len(path.split('/')) + 1):
            sub_path = '/'.join(path.split('/')[:i])

            if not self.irods.collections.exists(sub_path):
                self.irods.collections.create(sub_path)
                self.execute_data['created_colls'].append(sub_path)
                self.data_modified = True

        super(CreateCollectionTask, self).execute(*args, **kwargs)

    def revert(self, path, *args, **kwargs):
        if self.data_modified:
            for coll_path in reversed(self.execute_data['created_colls']):
                if self.irods.collections.exists(coll_path):
                    self.irods.collections.remove(coll_path, recurse=True)


# TODO: Refactor this as follows: Before removing, set a random metadata value
# TODO:     for the collection. If reverting, search for the version of the
# TODO:     deleted collection with the tag, recover that and remove the tag.
class RemoveCollectionTask(IrodsBaseTask):
    """Remove a collection if it exists (irm)"""

    # NOTE: Instead of using irm, move manually to trash with a specific name
    #       So we can be sure to recover the correct structure on revert
    #       (if collections with the same path are removed, they are collected
    #       in trash versioned with a timestamp, which we can't know for sure)
    def execute(self, path, *args, **kwargs):
        trash_path = '/' + path.split('/')[1] + '/trash/' + ''.join(
            random.SystemRandom().choice(
                string.ascii_lowercase + string.digits) for x in range(16))

        if self.irods.collections.exists(path):
            self.irods.collections.create(trash_path)   # Must create this 1st

            try:
                self.irods.collections.move(
                    src_path=path,
                    dest_path=trash_path)

            # NOTE: iRODS/client doesn't like to return a proper exception here
            except Exception as ex:
                pass

            # ..so let's test success manually just to be sure
            new_path = trash_path + '/' + path.split('/')[-1]

            if self.irods.collections.exists(new_path):
                self.data_modified = True
                self.execute_data['trash_path'] = trash_path

            else:
                raise Exception('Failed to remove collection')

        super(RemoveCollectionTask, self).execute(*args, **kwargs)

    def revert(self, path, *args, **kwargs):
        if self.data_modified:
            src_path = self.execute_data[
                'trash_path'] + '/' + path.split('/')[-1]
            dest_path = '/'.join(path.split('/')[:-1])

            self.irods.collections.move(
                src_path=src_path,
                dest_path=dest_path)

            # Delete temp trash collection
            self.irods.collections.remove(self.execute_data['trash_path'])


# TODO: Do we need to add several metadata items until the same key? If so,
# TODO:     A separate task should be created
class SetCollectionMetadataTask(IrodsBaseTask):
    """Set new value to existing metadata item (imeta set). NOTE: will replace
    existing value with the same name"""

    def execute(self, path, name, value, units=None, *args, **kwargs):
        coll = self.irods.collections.get(path)
        meta_item = None

        try:
            meta_item = coll.metadata.get_one(name)

        except Exception:   # Can't get proper Exception here
            pass

        if meta_item and value != meta_item.value:
            self.execute_data['value'] = str(meta_item.value)
            self.execute_data['units'] = str(meta_item.units)\
                if meta_item.units else None

            meta_item.value = str(value)
            meta_item.units = str(units)

            self.irods.metadata.set(
                model_cls=Collection,
                path=path,
                meta=meta_item)
            self.data_modified = True

        elif not meta_item:
            coll.metadata.add(str(name), str(value), str(units))
            self.data_modified = True

        super(SetCollectionMetadataTask, self).execute(*args, **kwargs)

    def revert(self, path, name, value, units=None, *args, **kwargs):
        if self.data_modified:
            coll = self.irods.collections.get(path)

            if self.execute_data:
                meta_item = coll.metadata.get_one(name)
                meta_item.value = str(self.execute_data['value'])
                meta_item.units = str(self.execute_data['units'])

                self.irods.metadata.set(
                    model_cls=Collection,
                    path=path,
                    meta=meta_item)

            else:
                coll.metadata.remove(name, str(value), units)


class CreateUserGroupTask(IrodsBaseTask):
    """Create user group if it doesn't exist (iadmin mkgroup)"""

    def execute(self, name, *args, **kwargs):
        try:
            self.irods.user_groups.get(name)

        except UserGroupDoesNotExist:
            self.irods.user_groups.create(
                name=name,
                user_zone=self.irods.zone)
            self.data_modified = True

        super(CreateUserGroupTask, self).execute(*args, **kwargs)

    def revert(self, name, *args, **kwargs):
        if self.data_modified:
            # NOTE: Not group_name
            self.irods.user_groups.remove(user_name=name)


class SetAccessTask(IrodsBaseTask):
    """Set user/group access to target (ichmod)"""

    def execute(self, access_name, path, user_name, *args, **kwargs):
        coll = self.irods.collections.get(path)
        coll_access = self.irods.permissions.get(target=coll)
        user_access = next(
            (x for x in coll_access if x.user_name == user_name), None)

        if (user_access and
                user_access.access_name != ACCESS_CONVERSION[access_name]):
            self.execute_data['access_name'] = ACCESS_CONVERSION[
                user_access.access_name]
            self.data_modified = True

        elif not user_access:
            self.execute_data['access_name'] = 'null'
            self.data_modified = True

        if self.data_modified:
            acl = iRODSAccess(
                access_name=access_name,
                path=path,
                user_name=user_name,
                user_zone=self.irods.zone)
            self.irods.permissions.set(acl, recursive=True)

        super(SetAccessTask, self).execute(*args, **kwargs)

    def revert(self, access_name, path, user_name, *args, **kwargs):
        if self.data_modified:
            acl = iRODSAccess(
                access_name=self.execute_data['access_name'],
                path=path,
                user_name=user_name,
                user_zone=self.irods.zone)
            self.irods.permissions.set(acl, recursive=True)


class CreateUserTask(IrodsBaseTask):
    """Create user if it does not exist (iadmin mkuser)"""
    # NOTE: Password not needed as users log in via LDAP

    def execute(self, user_name, user_type, *args, **kwargs):
        try:
            self.irods.users.get(user_name)

        except UserDoesNotExist:
            self.irods.users.create(
                user_name=user_name,
                user_type=user_type,
                user_zone=self.irods.zone)
            self.data_modified = True

        super(CreateUserTask, self).execute(*args, **kwargs)

    def revert(self, user_name, user_type, *args, **kwargs):
        # Remove user only if it was added in this run
        if self.data_modified:
            self.irods.users.remove(user_name)


class AddUserToGroupTask(IrodsBaseTask):
    """Add user to group if not yet added (iadmin atg)"""

    def execute(self, group_name, user_name, *args, **kwargs):
        try:
            group = self.irods.user_groups.get(group_name)

            if not group.hasmember(user_name):
                group.addmember(
                    user_name=user_name,
                    user_zone=self.irods.zone)
                self.data_modified = True

        except Exception as ex:
            self._raise_irods_execption(ex)

        super(AddUserToGroupTask, self).execute(*args, **kwargs)

    def revert(self, group_name, user_name, *args, **kwargs):
        if self.data_modified:
            group = self.irods.user_groups.get(group_name)
            group.removemember(
                user_name=user_name,
                user_zone=self.irods.zone)


class RemoveUserFromGroupTask(IrodsBaseTask):
    """Remove user from group (iadmin rfg)"""

    def execute(self, group_name, user_name, *args, **kwargs):
        try:
            group = self.irods.user_groups.get(group_name)

            if group.hasmember(user_name):
                group.removemember(
                    user_name=user_name,
                    user_zone=self.irods.zone)
                self.data_modified = True

        except Exception as ex:
            self._raise_irods_execption(ex)

        super(RemoveUserFromGroupTask, self).execute(*args, **kwargs)

    def revert(self, group_name, user_name, *args, **kwargs):
        if self.data_modified:
            group = self.irods.user_groups.get(group_name)
            group.addmember(
                user_name=user_name,
                user_zone=self.irods.zone)


# TODO: Improve this to accept both obj/collection for dest_path in revert
class MoveDataObjectTask(IrodsBaseTask):
    """Move file to destination collection (imv)"""

    def execute(self, src_path, dest_path, *args, **kwargs):
        try:
            self.irods.data_objects.move(
                src_path=src_path,
                dest_path=dest_path)
            self.data_modified = True

        except Exception as ex:
            self._raise_irods_execption(ex)

        super(MoveDataObjectTask, self).execute(*args, **kwargs)

    def revert(self, src_path, dest_path, *args, **kwargs):
        if self.data_modified:
            # TODO: First check if final item in path is obj or coll
            new_src = dest_path + '/' + src_path.split('/')[-1]
            new_dest = '/'.join(src_path.split('/')[:-1])

            self.irods.data_objects.move(
                src_path=new_src,
                dest_path=new_dest)


class ValidateDataObjectChecksumTask(IrodsBaseTask):
    """Validate data object checksum by accompanying .md5 file"""
    # NOTE: This is a temporary hack for the demo, real validation will be done
    #       elsewhere (e.g. directly in iRODS rules)
    def execute(self, path, *args, **kwargs):
        try:
            md5_path = path + '.md5'
            md5_file = self.irods.data_objects.open(md5_path, mode='r')
            file_sum = md5_file.read().decode('utf-8').split(' ')[0]
            file_obj = self.irods.data_objects.get(path)

            if file_sum != file_obj.checksum:
                print('Checksums do not match for "{}"!'.format(
                    path.split('/')[-1]))    # DEBUG
                raise Exception('Checksums do not match for "{}"'.format(
                    path.split('/')[-1]))

        except Exception as ex:
            self._raise_irods_execption(ex)

        super(ValidateDataObjectChecksumTask, self).execute(*args, **kwargs)

    def revert(self, path, *args, **kwargs):
        pass    # Nothing is modified so no need for revert
