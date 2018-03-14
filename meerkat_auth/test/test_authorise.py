# !/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the authorise.py module in Meerkat Auth
"""
from werkzeug import exceptions
from meerkat_auth.user import User
from meerkat_auth.authorise import Authorise
from meerkat_auth import app
from meerkat_libs import db_adapters
from unittest import mock
import unittest
import calendar
import time
import logging
import os
import importlib.util

# Load the secret settings module where the JWT details are stored.
filename = os.environ.get('MEERKAT_AUTH_SETTINGS')
spec = importlib.util.spec_from_file_location("settings", filename)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class MeerkatAuthAuthoriseTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        app.config.from_object('meerkat_auth.config.Testing')
        app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
        # Mock the db
        app.db = mock.create_autospec(db_adapters.DynamoDBAdapter)
        self.db_data = {
            app.config['ROLES']: {},
            app.config['USERS']: {}
        }

        def build_key(keys):
            return '-'.join(["{}:{}".format(k, v) for (k, v) in keys.items()])

        def read_effect(table, keys, attributes=[]):
            item = self.db_data[table].get(build_key(keys), {})
            return {k: item[k] for k in item if k not in attributes}

        def write_effect(table, keys, attributes):
            self.db_data[table][build_key(keys)] = {**attributes, **keys}

        def delete_effect(table, keys):
            print(self.db_data[table][build_key(keys)])
            del self.db_data[table][build_key(keys)]

        app.db.read.side_effect = read_effect
        app.db.write.side_effect = write_effect
        app.db.delete.side_effect = delete_effect

        # Initialise the db
        roles = [
            {'country': 'demo', 'role': 'clinic',
             'description': 'clinic.', 'parents': []},
            {'country': 'demo', 'role': 'personal',
             'description': 'Personal.', 'parents': []},
            {'country': 'demo', 'role': 'directorate',
             'description': 'directorate.', 'parents': ['clinic']},
            {'country': 'jordan', 'role': 'clinic',
             'description': 'Registered.', 'parents': []},
            {'country': 'jordan', 'role': 'directorate',
             'description': 'directorate.', 'parents': ['clinic']},
            {'country': 'jordan', 'role': 'central',
             'description': 'central.', 'parents': ['directorate']},
            {'country': 'jordan', 'role': 'personal',
             'description': 'Personal.', 'parents': []},
            {'country': 'jordan', 'role': 'admin',
             'description': 'admin.', 'parents': ['personal']}
        ]
        for role in roles:
            keys = {'country': role['country'], 'role': role['role']}
            write_effect(
                app.config['ROLES'],
                keys,
                {k: role[k] for k in role if k not in keys}
            )

        users = [
            {'username': 'testUser1',
             'email': 'test1@test.org.uk',
             'password': User.hash_password('password1'),
             'countries': ['jordan'],
             'roles': ['directorate'],
             'data': {'name': 'Testy McTestface'}},
            {'username': 'testUser2',
             'email': 'test2@test.org.uk',
             'password': User.hash_password('password2'),
             'countries': ['demo', 'jordan', 'jordan'],
             'roles': ['directorate', 'central', 'personal'],
             'data': {'name': 'Tester McTestface'}}
        ]

        for user in users:
            keys = {'username': user['username']}
            write_effect(
                app.config['USERS'],
                keys,
                {k: user[k] for k in user if k not in keys}
            )

        self.auth = Authorise()

    def test_get_token(self):
        """Test the get_token() function."""

        # get_token() looks in both the cookie and authorization headers.
        auth_h = {'Authorization': 'Bearer headertoken'}
        cookie_h = {'Cookie': settings.JWT_COOKIE_NAME + '=cookietoken'}

        # Check that function responds correctly to the different headers.
        with app.test_request_context('/', headers=auth_h):
            self.assertEqual(self.auth.get_token(), 'headertoken')
        with app.test_request_context('/', headers=cookie_h):
            self.assertEqual(self.auth.get_token(), 'cookietoken')
        with app.test_request_context('/', headers={**auth_h, **cookie_h}):
            self.assertEqual(self.auth.get_token(), 'cookietoken')
        with app.test_request_context('/', headers={}):
            self.assertEqual(self.auth.get_token(), '')

    def test_check_access(self):
        """Test the check_access() function. Really important test!"""

        # Access to one level in one country that inherits one level.
        acc = User.from_db('testUser1').get_access()
        logging.warning(acc)

        self.assertTrue(self.auth.check_access(
            [''], [''], acc
        ))
        self.assertTrue(self.auth.check_access(
            [''], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['directorate'], [''], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['directorate'], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['clinic'], ['jordan'], acc
        ))
        self.assertFalse(self.auth.check_access(
            [''], ['demo'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['central'], [''], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['admin'], ['jordan'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['central'], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['directorate', 'admin'], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['directorate', 'admin'], ['jordan', 'jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['directorate', 'clinic'], ['jordan', 'demo'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['central', 'admin'], ['jordan'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['central', 'admin'], ['jordan', 'jordan'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['directorate', 'clinic'], ['demo', 'demo'], acc
        ))

        # Access to many levels in many countries with many inherited levels.
        acc = User.from_db('testUser2').get_access()
        logging.warning(acc)

        self.assertTrue(self.auth.check_access(
            [''], [''], acc
        ))
        self.assertTrue(self.auth.check_access(
            [''], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            [''], ['demo'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['personal'], [''], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['central'], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['clinic'], ['jordan'], acc
        ))
        self.assertFalse(self.auth.check_access(
            [''], ['random'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['root'], [''], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['admin'], ['jordan'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['central'], ['demo'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['admin', 'root'], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['root', 'directorate'], ['jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['root', 'clinic'], ['jordan', 'jordan'], acc
        ))
        self.assertTrue(self.auth.check_access(
            ['root', 'clinic'], ['jordan', 'demo'], acc
        ))
        self.assertFalse(self.auth.check_access(
            ['admin', 'central'], ['jordan', 'demo'], acc
        ))

    def test_check_auth(self):
        """Test the check_auth() function."""

        # Make a request with no token.
        with app.test_request_context('/'):
            # Check that a 401 error is raised if no token is found
            self.assertRaises(
                exceptions.Unauthorized,
                lambda: self.auth.check_auth(['directorate'], ['jordan'])
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
                lambda: self.auth.check_auth(['central'], ['jordan'])
            )

        # Create an expired token to try and authenticate the request.
        u = User.from_db('testUser1')
        token = u.get_jwt(calendar.timegm(time.gmtime()) - 1).decode('UTF-8')
        cookie_headers = {'Cookie': settings.JWT_COOKIE_NAME + "=" + token}

        # Make a request using the expired token
        with app.test_request_context('/', headers=cookie_headers):
            # 403 error should be raised trying to exceed users access levels.
            self.assertRaises(
                exceptions.Forbidden,
                lambda: self.auth.check_auth(['directorate'], ['jordan'])
            )
