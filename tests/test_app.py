"""Tests for web app requests"""
from unittest import TestCase

import sodar_taskflow
from apis.irods_utils import init_irods, cleanup_irods


class AppTestBase(TestCase):
    """Base test class for web app"""

    def setUp(self):
        # Init iRODS connection
        self.irods = init_irods()
        self.app = sodar_taskflow.app.test_client()
        pass

    def tearDown(self):
        # Remove leftover data from iRODS
        cleanup_irods(self.irods, verbose=False)
        pass


class TestHello(AppTestBase):
    """Tests for the hello world page"""
    def test_hello_render(self):
        """Test rendering of hello page (to ensure we can connect to app)"""
        # url = settings.SERVER_NAME + '/hello'
        response = self.app.get('/hello')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'Hello world from sodar_taskflow!')

# TODO: Tests for submit & cleanup
