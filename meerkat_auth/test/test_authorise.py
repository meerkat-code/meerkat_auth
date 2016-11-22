# !/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the authorise.py module in Meerkat Auth
"""
from werkzeug import exceptions
from meerkat_auth.user import User
from meerkat_auth.role import Role
from meerkat_auth import authorise as auth
from meerkat_auth import app
import unittest
import calendar
import time
import logging
import boto3
import os

# Hacky!
# Need this module to be importable without the whole of meerkat_auth config.
# Directly load secret settings file from which to import required config.
# File must define JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables.
filename = os.environ.get('MEERKAT_AUTH_SETTINGS')
exec(compile(open(filename, "rb").read(), filename, 'exec'))


class MeerkatAuthAuthoriseTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        app.config['TESTING'] = True
        app.config['USERS'] = 'test_auth_users'
        app.config['ROLES'] = 'test_auth_roles'
        app.config['DB_URL'] = 'https://dynamodb.eu-west-1.amazonaws.com'
        User.DB = boto3.resource(
            'dynamodb',
            endpoint_url="https://dynamodb.eu-west-1.amazonaws.com",
            region_name='eu-west-1'
        )
        Role.DB = boto3.resource(
            'dynamodb',
            endpoint_url="https://dynamodb.eu-west-1.amazonaws.com",
            region_name='eu-west-1'
        )
        self.app = app.test_client()
        logging.warning(app.config['DB_URL'])
        # The database should have the following objects already in it.
        roles = [
            Role('demo', 'clinic', 'clinic description.', []),
            Role('demo', 'directorate', 'Directorate', ['clinic']),
            Role('demo', 'central', 'Central.', ['directorate']),
            Role('jordan', 'clinic', 'Clinic description.', []),
            Role('jordan', 'directorate', 'Directorate.', ['clinic']),
            Role('jordan', 'central', 'Central description.', ['directorate']),
            Role('jordan', 'personal', 'directorate description.', []),
            Role('jordan', 'admin', 'Backend access.', ['personal'])
        ]

        # Update objects in case something else spuriously changed them.
        for role in roles:
            role.to_db()

        # Put into the database a couple of test users.
        users = [
            User(
                'testUser1',
                'test1@test.org.uk',
                User.hash_password('password1'),
                ['jordan'],
                ['directorate'],
                data={
                    'name': 'Testy McTestface'
                }
            ),
            User(
                'testUser2',
                'test2@test.org.uk',
                User.hash_password('password2'),
                ['demo', 'jordan', 'jordan'],
                ['directorate', 'central', 'personal'],
                data={
                    'name': 'Tester McTestFace'
                }
            )
        ]
        for user in users:
            user.to_db()

    def tearDown(self):
        """Tear down after testing."""
        User.delete('testUser')

    def test_get_token(self):
        """Test the get_token() function."""

        # get_token() looks in both the cookie and authorization headers.
        auth_h = {'Authorization': 'Bearer headertoken'}
        cookie_h = {'Cookie': JWT_COOKIE_NAME + '=cookietoken'}

        # Check that function responds correctly to the different headers.
        with app.test_request_context('/', headers=auth_h):
            self.assertEqual(auth.get_token(), 'headertoken')
        with app.test_request_context('/', headers=cookie_h):
            self.assertEqual(auth.get_token(), 'cookietoken')
        with app.test_request_context('/', headers={**auth_h, **cookie_h}):
            self.assertEqual(auth.get_token(), 'cookietoken')
        with app.test_request_context('/', headers={}):
            self.assertEqual(auth.get_token(), '')

    def test_check_access(self):
        """Test the check access function. Really important test!"""

        # Access to one level in one country that inherits one level.
        acc = User.from_db('testUser1').get_access()
        logging.warning(acc)

        self.assertTrue(auth.check_access([''], [''], acc))
        self.assertTrue(auth.check_access([''], ['jordan'], acc))
        self.assertTrue(auth.check_access(['directorate'], [''], acc))
        self.assertTrue(auth.check_access(['directorate'], ['jordan'], acc))
        self.assertTrue(auth.check_access(['clinic'], ['jordan'], acc))
        self.assertFalse(auth.check_access([''], ['demo'], acc))
        self.assertFalse(auth.check_access(['central'], [''], acc))
        self.assertFalse(auth.check_access(['admin'], ['jordan'], acc))
        self.assertFalse(auth.check_access(['central'], ['jordan'], acc))
        self.assertTrue(
            auth.check_access(['directorate', 'admin'], ['jordan'], acc)
        )
        self.assertTrue(auth.check_access(
            ['directorate', 'admin'], ['jordan', 'jordan'], acc)
        )
        self.assertTrue(auth.check_access(
            ['directorate', 'clinic'], ['jordan', 'demo'], acc)
        )
        self.assertFalse(
            auth.check_access(['central', 'admin'], ['jordan'], acc)
        )
        self.assertFalse(
            auth.check_access(['central', 'admin'], ['jordan', 'jordan'], acc)
        )
        self.assertFalse(
            auth.check_access(['directorate', 'clinic'], ['demo', 'demo'], acc)
        )

        # Access to many levels in many countries with many inherited levels.
        acc = User.from_db('testUser2').get_access()
        logging.warning(acc)

        self.assertTrue(auth.check_access([''], [''], acc))
        self.assertTrue(auth.check_access([''], ['jordan'], acc))
        self.assertTrue(auth.check_access([''], ['demo'], acc))
        self.assertTrue(auth.check_access(['personal'], [''], acc))
        self.assertTrue(auth.check_access(['central'], ['jordan'], acc))
        self.assertTrue(auth.check_access(['clinic'], ['jordan'], acc))
        self.assertFalse(auth.check_access([''], ['random'], acc))
        self.assertFalse(auth.check_access(['root'], [''], acc))
        self.assertFalse(auth.check_access(['admin'], ['jordan'], acc))
        self.assertFalse(auth.check_access(['central'], ['demo'], acc))
        self.assertFalse(auth.check_access(['admin', 'root'], ['jordan'], acc))
        self.assertTrue(
            auth.check_access(['root', 'directorate'], ['jordan'], acc)
        )
        self.assertTrue(
            auth.check_access(['root', 'clinic'], ['jordan', 'jordan'], acc)
        )
        self.assertTrue(
            auth.check_access(['root', 'clinic'], ['jordan', 'demo'], acc)
        )
        self.assertFalse(
            auth.check_access(['admin', 'central'], ['jordan', 'demo'], acc)
        )

    def test_check_auth(self):
        """Test the check_auth function."""

        # Make a request with no token.
        with app.test_request_context('/'):
            # Check that a 401 error is raised if no token is found
            self.assertRaises(
                exceptions.Unauthorized,
                lambda: auth.check_auth(['directorate'], ['jordan'])
            )

        # Create a token to authenticate the request.
        u = User.from_db('testUser1')
        token = u.get_jwt(calendar.timegm(time.gmtime()) + 30).decode('UTF-8')
        auth_headers = {'Authorization': 'Bearer ' + token}

        # Make a request using testUser1
        with app.test_request_context('/', headers=auth_headers):
            # 403 error should be raised trying to exceed users access levels.
            self.assertRaises(
                exceptions.Forbidden,
                lambda: auth.check_auth(['central'], ['jordan'])
            )

        # Create an expired token to try and authenticate the request.
        u = User.from_db('testUser1')
        token = u.get_jwt(calendar.timegm(time.gmtime()) - 1).decode('UTF-8')
        cookie_headers = {'Cookie': JWT_COOKIE_NAME + "=" + token}

        # Make a request using the expired token
        with app.test_request_context('/', headers=cookie_headers):
            # 403 error should be raised trying to exceed users access levels.
            self.assertRaises(
                exceptions.Forbidden,
                lambda: auth.check_auth(['directorate'], ['jordan'])
            )
