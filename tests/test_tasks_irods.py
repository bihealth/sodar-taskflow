import os
import uuid

from irods.access import iRODSAccess
from irods.collection import iRODSCollection
from irods.exception import CollectionDoesNotExist, UserDoesNotExist,\
    UserGroupDoesNotExist, NoResultFound
from irods.meta import iRODSMeta
from irods.models import Collection
from irods.user import iRODSUser, iRODSUserGroup

from unittest import TestCase

from apis.irods_utils import init_irods, cleanup_irods
from config import settings
from flows.base_flow import BaseLinearFlow
from tasks.irods_tasks import *

USER_PREFIX = 'omics_'

IRODS_ZONE = settings.TASKFLOW_IRODS_ZONE
DEFAULT_USER_GROUP = USER_PREFIX + 'group1'

GROUP_USER = USER_PREFIX + 'user1'
GROUPLESS_USER = USER_PREFIX + 'user2'

ROOT_COLL = '/{}/projects'.format(IRODS_ZONE)
TEST_COLL = '{}/test'.format(ROOT_COLL)
TEST_COLL_NEW = '{}/test_new'.format(ROOT_COLL)

TEST_USER = USER_PREFIX + 'user3'
TEST_USER_TYPE = 'rodsuser'
TEST_KEY = 'test_key'
TEST_VAL = 'test_val'
TEST_UNITS = 'test_units'
TEST_USER_GROUP = USER_PREFIX + 'group2'

# NOTE: Yes, we really need this for the python irods client
TEST_ACCESS_READ_IN = 'read'
TEST_ACCESS_READ_OUT = 'read object'
TEST_ACCESS_WRITE_IN = 'write'
TEST_ACCESS_WRITE_OUT = 'modify object'
TEST_ACCESS_NULL = 'null'


class IRODSTestBase(TestCase):
    """Base test class for iRODS tasks"""

    def setUp(self):
        # Init iRODS connection
        self.irods = init_irods()

        # HACK: Avoiding exceptions which may result to tearDown not getting
        #       called and unwanted objects being left in iRODS
        try:
            # Init default collections
            self.irods.collections.create(ROOT_COLL)
            self.irods.collections.create(TEST_COLL)

            # Init default user group
            group = self.irods.user_groups.create(DEFAULT_USER_GROUP)

            # Init default users
            self.irods.users.create(
                user_name=GROUP_USER,
                user_type='rodsuser',
                user_zone=IRODS_ZONE)
            group.addmember(GROUP_USER)

            self.irods.users.create(
                user_name=GROUPLESS_USER,
                user_type='rodsuser',
                user_zone=IRODS_ZONE)

        except Exception as ex:
            print('setUp failed: {}'.format(ex))

        # Init flow
        self.flow = self._init_flow()

    def tearDown(self):
        # Remove leftover data from iRODS
        cleanup_irods(self.irods, verbose=False)

    def _run_flow(self):
        # print('\n')  # HACK to fix lack of newline in test output :)
        return self.flow.run(verbose=False)

    def _init_flow(self):
        return BaseLinearFlow(
            irods=self.irods,
            omics_api=None,
            project_pk=1,
            flow_name=str(uuid.uuid4()),
            flow_data={},
            targets=['irods'])

    def _add_task(self, cls, name, inject, force_fail=False):
        self.flow.add_task(cls(
            name=name,
            irods=self.irods,
            verbose=False,
            inject=inject,
            force_fail=force_fail))

    def _get_root_coll(self):
        return self.irods.collections.get(ROOT_COLL)

    def _get_test_coll(self):
        return self.irods.collections.get(TEST_COLL)

    def _get_user_access(self, target, user_name):
        target_access = self.irods.permissions.get(target=target)
        return next(
            (x for x in target_access if x.user_name == user_name), None)


class TestCreateCollectionTask(IRODSTestBase):
    def test_execute(self):
        """Test collection creation"""
        self._add_task(
            cls=CreateCollectionTask,
            name='Create collection',
            inject={'path': TEST_COLL_NEW})

        # Assert precondition
        self.assertRaises(
            CollectionDoesNotExist,
            self.irods.collections.get,
            TEST_COLL_NEW)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        coll = self.irods.collections.get(TEST_COLL_NEW)
        self.assertIsInstance(coll, iRODSCollection)

    def test_execute_twice(self):
        """Test collection creation twice"""
        self._add_task(
            cls=CreateCollectionTask,
            name='Create collection',
            inject={'path': TEST_COLL_NEW})

        result = self._run_flow()

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=CreateCollectionTask,
            name='Create collection',
            inject={'path': TEST_COLL_NEW})
        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        coll = self.irods.collections.get(TEST_COLL_NEW)
        self.assertIsInstance(coll, iRODSCollection)

    def test_revert_created(self):
        """Test collection creation reverting after creating"""
        self._add_task(
            cls=CreateCollectionTask,
            name='Create collection',
            inject={'path': TEST_COLL_NEW},
            force_fail=True)    # FAIL

        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        self.assertRaises(
            CollectionDoesNotExist,
            self.irods.collections.get,
            TEST_COLL_NEW)

    def test_revert_not_modified(self):
        """Test collection creation reverting without modification"""
        self._add_task(
            cls=CreateCollectionTask,
            name='Create collection',
            inject={'path': TEST_COLL_NEW})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=CreateCollectionTask,
            name='Create collection',
            inject={'path': TEST_COLL_NEW},
            force_fail=True)    # FAIL
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        coll = self.irods.collections.get(TEST_COLL_NEW)
        self.assertIsInstance(coll, iRODSCollection)


class TestSetCollectionMetadataTask(IRODSTestBase):
    def test_execute(self):
        """Test setting metadata"""
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': TEST_VAL,
                'units': TEST_UNITS})

        test_coll = self._get_test_coll()

        # Assert precondition
        self.assertRaises(
            Exception,
            test_coll.metadata.get_one,
            TEST_KEY)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        # NOTE: We must retrieve collection again to refresh its metadata
        test_coll = self._get_test_coll()
        meta_item = test_coll.metadata.get_one(TEST_KEY)
        self.assertIsInstance(meta_item, iRODSMeta)
        self.assertEqual(meta_item.name, TEST_KEY)
        self.assertEqual(meta_item.value, TEST_VAL)
        self.assertEqual(meta_item.units, TEST_UNITS)

    def test_execute_twice(self):
        """Test setting metadata twice"""
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': TEST_VAL,
                'units': TEST_UNITS})

        result = self._run_flow()

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': TEST_VAL,
                'units': TEST_UNITS})
        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        test_coll = self._get_test_coll()
        meta_item = test_coll.metadata.get_one(TEST_KEY)
        self.assertIsInstance(meta_item, iRODSMeta)

    def test_revert_created(self):
        """Test metadata setting reverting after creating a new item"""
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': TEST_VAL,
                'units': TEST_UNITS},
            force_fail=True)    # FAIL

        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        test_coll = self._get_test_coll()
        self.assertRaises(
            KeyError,
            test_coll.metadata.get_one,
            TEST_KEY)

    def test_revert_modified(self):
        """Test metadata setting reverting after modification"""
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': TEST_VAL,
                'units': TEST_UNITS})

        result = self._run_flow()

        # Init and run new flow
        self.flow = self._init_flow()
        new_val = 'new value'
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': new_val,
                'units': TEST_UNITS},
            force_fail=True)  # FAIL
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        test_coll = self._get_test_coll()
        meta_item = test_coll.metadata.get_one(TEST_KEY)
        self.assertIsInstance(meta_item, iRODSMeta)
        self.assertEqual(meta_item.value, TEST_VAL)    # Original value

    def test_revert_not_modified(self):
        """Test metadata setting reverting without modification"""
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': TEST_VAL,
                'units': TEST_UNITS})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=SetCollectionMetadataTask,
            name='Set metadata',
            inject={
                'path': TEST_COLL,
                'name': TEST_KEY,
                'value': TEST_VAL,
                'units': TEST_UNITS},
            force_fail=True)
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        test_coll = self._get_test_coll()
        self.assertIsInstance(test_coll, iRODSCollection)


class TestCreateUserGroupTask(IRODSTestBase):
    def test_execute(self):
        """Test user group creation"""
        self._add_task(
            cls=CreateUserGroupTask,
            name='Create user group',
            inject={'name': TEST_USER_GROUP})

        # Assert precondition
        self.assertRaises(
            UserGroupDoesNotExist,
            self.irods.user_groups.get,
            TEST_USER_GROUP)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(TEST_USER_GROUP)
        self.assertIsInstance(group, iRODSUserGroup)

    def test_execute_twice(self):
        """Test user group creation twice"""
        self._add_task(
            cls=CreateUserGroupTask,
            name='Create user group',
            inject={'name': TEST_USER_GROUP})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=CreateUserGroupTask,
            name='Create user group',
            inject={'name': TEST_USER_GROUP})
        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(TEST_USER_GROUP)
        self.assertIsInstance(group, iRODSUserGroup)

    def test_revert_created(self):
        """Test collection creation reverting after creation"""
        self._add_task(
            cls=CreateUserGroupTask,
            name='Create user group',
            inject={'name': TEST_USER_GROUP},
            force_fail=True)    # FAIL

        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        self.assertRaises(
            UserGroupDoesNotExist,
            self.irods.user_groups.get,
            TEST_USER_GROUP)

    def test_revert_not_modified(self):
        """Test collection creation reverting without modification"""
        self._add_task(
            cls=CreateUserGroupTask,
            name='Create user group',
            inject={'name': TEST_USER_GROUP})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=CreateUserGroupTask,
            name='Create user group',
            inject={'name': TEST_USER_GROUP},
            force_fail=True)    # FAIL
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(TEST_USER_GROUP)
        self.assertIsInstance(group, iRODSUserGroup)


class TestSetAccessTask(IRODSTestBase):
    def test_execute_read(self):
        """Test access setting for read"""
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_READ_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP})

        # Assert precondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertEqual(user_access, None)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertIsInstance(user_access, iRODSAccess)
        self.assertEqual(user_access.access_name, TEST_ACCESS_READ_OUT)

    def test_execute_write(self):
        """Test access setting for write/modify"""
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_WRITE_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP})

        # Assert precondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertEqual(user_access, None)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertIsInstance(user_access, iRODSAccess)
        self.assertEqual(user_access.access_name, TEST_ACCESS_WRITE_OUT)

    def test_execute_twice(self):
        """Test access setting twice"""
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_READ_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_READ_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP})
        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertIsInstance(user_access, iRODSAccess)
        self.assertEqual(user_access.access_name, TEST_ACCESS_READ_OUT)

    def test_revert_created(self):
        """Test access setting"""
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_READ_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP},
            force_fail=True)    # FAIL

        result = self._run_flow()

        # Assert flow success
        self.assertNotEqual(result, True)

        # Assert postcondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertIsNone(user_access)
        # self.assertEqual(user_access.access_name, TEST_ACCESS_NULL)

    def test_revert_modified(self):
        """Test access setting reverting after modification"""
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_READ_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP})

        result = self._run_flow()

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_WRITE_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP},
            force_fail=True)    # FAIL
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertIsInstance(user_access, iRODSAccess)
        self.assertEqual(user_access.access_name, TEST_ACCESS_READ_OUT)

    def test_revert_not_modified(self):
        """Test access setting reverting without modification"""
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_READ_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=SetAccessTask,
            name='Set access',
            inject={
                'access_name': TEST_ACCESS_READ_IN,
                'path': TEST_COLL,
                'user_name': DEFAULT_USER_GROUP},
            force_fail=True)  # FAIL
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        user_access = self._get_user_access(
            target=self._get_test_coll(),
            user_name=DEFAULT_USER_GROUP)
        self.assertIsInstance(user_access, iRODSAccess)
        self.assertEqual(user_access.access_name, TEST_ACCESS_READ_OUT)


class TestCreateUserTask(IRODSTestBase):
    def test_execute(self):
        """Test user creation"""
        self._add_task(
            cls=CreateUserTask,
            name='Create user',
            inject={
                'user_name': TEST_USER,
                'user_type': TEST_USER_TYPE})

        # Assert precondition
        self.assertRaises(
            UserDoesNotExist,
            self.irods.users.get,
            TEST_USER)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        user = self.irods.users.get(TEST_USER)
        self.assertIsInstance(user, iRODSUser)

    def test_execute_twice(self):
        """Test user creation twice"""
        self._add_task(
            cls=CreateUserTask,
            name='Create user',
            inject={
                'user_name': TEST_USER,
                'user_type': TEST_USER_TYPE})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=CreateUserTask,
            name='Create user',
            inject={
                'user_name': TEST_USER,
                'user_type': TEST_USER_TYPE})
        result = self._run_flow()

        # Assert postcondition
        user = self.irods.users.get(TEST_USER)
        self.assertIsInstance(user, iRODSUser)

    def test_revert_created(self):
        """Test user creation reverting after creating"""
        self._add_task(
            cls=CreateUserTask,
            name='Create user',
            inject={
                'user_name': TEST_USER,
                'user_type': TEST_USER_TYPE},
            force_fail=True)    # FAIL

        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        self.assertRaises(
            UserDoesNotExist,
            self.irods.users.get,
            TEST_USER)

    def test_revert_not_modified(self):
        """Test user creation reverting without modification"""
        self._add_task(
            cls=CreateUserTask,
            name='Create user',
            inject={
                'user_name': TEST_USER,
                'user_type': TEST_USER_TYPE})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=CreateUserTask,
            name='Create user',
            inject={
                'user_name': TEST_USER,
                'user_type': TEST_USER_TYPE},
            force_fail=True)    # FAIL
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        user = self.irods.users.get(TEST_USER)
        self.assertIsInstance(user, iRODSUser)


class TestAddUserToGroupTask(IRODSTestBase):
    def test_execute(self):
        """Test user addition"""
        self._add_task(
            cls=AddUserToGroupTask,
            name='Add user to group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUPLESS_USER})

        # Assert precondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUPLESS_USER), False)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUPLESS_USER), True)

    def test_execute_twice(self):
        """Test user addition twice"""
        self._add_task(
            cls=AddUserToGroupTask,
            name='Add user to group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUPLESS_USER})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=AddUserToGroupTask,
            name='Add user to group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUPLESS_USER})
        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUPLESS_USER), True)

    def test_revert_modified(self):
        """Test user addition reverting after modification"""
        self._add_task(
            cls=AddUserToGroupTask,
            name='Add user to group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUPLESS_USER},
            force_fail=True)  # FAILS
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUPLESS_USER), False)

    def test_revert_not_modified(self):
        """Test user addition reverting without modification"""
        self._add_task(
            cls=AddUserToGroupTask,
            name='Add user to group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUPLESS_USER})
        result = self._run_flow()

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=AddUserToGroupTask,
            name='Add user to group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUPLESS_USER},
            force_fail=True)    # FAILS
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUPLESS_USER), True)


class TestRemoveUserFromGroupTask(IRODSTestBase):
    def test_execute(self):
        """Test user addition"""
        self._add_task(
            cls=RemoveUserFromGroupTask,
            name='Remove user from group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUP_USER})

        # Assert precondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUP_USER), True)

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUP_USER), False)

    def test_execute_twice(self):
        """Test user addition twice"""
        self._add_task(
            cls=RemoveUserFromGroupTask,
            name='Remove user from group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUP_USER})

        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=RemoveUserFromGroupTask,
            name='Remove user from group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUP_USER})
        result = self._run_flow()

        # Assert flow success
        self.assertEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUP_USER), False)

    def test_revert_modified(self):
        """Test user addition reverting after modification"""
        self._add_task(
            cls=RemoveUserFromGroupTask,
            name='Remove user from group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUP_USER},
            force_fail=True)  # FAILS
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUP_USER), True)

    def test_revert_not_modified(self):
        """Test user addition reverting without modification"""
        self._add_task(
            cls=RemoveUserFromGroupTask,
            name='Remove user from group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUP_USER})
        result = self._run_flow()

        # Init and run new flow
        self.flow = self._init_flow()
        self._add_task(
            cls=RemoveUserFromGroupTask,
            name='Remove user from group',
            inject={
                'group_name': DEFAULT_USER_GROUP,
                'user_name': GROUP_USER},
            force_fail=True)    # FAILS
        result = self._run_flow()

        # Assert flow failure
        self.assertNotEqual(result, True)

        # Assert postcondition
        group = self.irods.user_groups.get(DEFAULT_USER_GROUP)
        self.assertEqual(group.hasmember(GROUP_USER), False)
