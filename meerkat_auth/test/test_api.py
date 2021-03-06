# !/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for REST API resources in Meerkat Auth.
"""
from meerkat_auth.user import User
from meerkat_auth.role import Role
from unittest import mock
from meerkat_auth import app
import meerkat_auth
import json
import unittest
import jwt
import calendar
import time
import logging
import boto3
import os


# Need this module to be importable without the whole of meerkat_auth config.
# Directly load secret settings file from which to import required config.
# File must define JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables.
filename = os.environ.get('MEERKAT_AUTH_SETTINGS')
exec(compile(open(filename, "rb").read(), filename, 'exec'))


class MeerkatAuthAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        app.config.from_object('meerkat_auth.config.Testing')
        app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
        User.DB = boto3.resource(
            'dynamodb',
            endpoint_url=app.config['DB_URL'],
            region_name='eu-west-1'
        )
        Role.DB = boto3.resource(
            'dynamodb',
            endpoint_url=app.config['DB_URL'],
            region_name='eu-west-1'
        )
        self.app = meerkat_auth.app.test_client()
        logging.warning(app.config['DB_URL'])
        # The database should have the following objects already in it
        roles = [
            Role('demo', 'registered', 'Registered description.', []),
            Role('demo', 'personal', 'Personal description.', ['registered']),
            Role('demo', 'shared', 'Shared description.', ['registered']),
            Role('demo', 'manager', 'Manager.', ['personal', 'shared']),
            Role('jordan', 'registered', 'Registered description.', []),
            Role('jordan', 'personal', 'Personal description.', ['registered'])
        ]

        # Update objects in case something else has spuriously has changed them
        for role in roles:
            role.to_db()

        # Put into the database a couple of test users
        users = [
            User(
                'testUser1',
                'test1@test.org.uk',
                User.hash_password('password1'),
                ['demo', 'jordan'],
                ['manager', 'personal'],
                data={
                    'name': 'Testy McTestface'
                },
                state='new'
            ),
            User(
                'testUser2',
                'test2@test.org.uk',
                User.hash_password('password2'),
                ['demo'],
                ['personal'],
                data={
                    'name': 'Tester McTestFace'
                },
                state='new'
            )
        ]
        for user in users:
            user.to_db()

    def tearDown(self):
        """Tear down after testing."""
        User.delete('testUser1')
        User.delete('testUser2')

    @mock.patch('flask.Response.set_cookie')
    def test_login(self, request_mock):
        """Test the login resource."""

        # Post some data to the login function and check successful behaviour
        post_data = json.dumps(
            {'username': 'testUser1', 'password': 'password1'}
        )
        post_response = self.app.post(
            '/api/login',
            data=post_data,
            content_type='application/json'
        )
        post_json = json.loads(post_response.data.decode('UTF-8'))
        response_jwt = request_mock.call_args[1]['value'].decode('UTF-8')

        self.assertEqual(post_json.get('message', ''), 'successful')
        self.assertTrue(request_mock.called)

        # Decode the jwt and check it is structured as expected.
        payload = jwt.decode(
            response_jwt,
            JWT_PUBLIC_KEY,
            algorithms=JWT_ALGORITHM
        )
        self.assertTrue(payload.get('usr', False))
        self.assertTrue(payload.get('exp', False))

        # Check the payload contents make sense.
        max_exp = calendar.timegm(time.gmtime()) + app.config['TOKEN_LIFE']
        self.assertTrue(payload['exp'] <= max_exp)
        self.assertEquals(payload['usr'], u'testUser1')

        # Now check that login fails for the wrong credentials.
        post_data = json.dumps(
            {'username': 'testUser1', 'password': 'password2'}
        )
        post_response = self.app.post(
            '/api/login',
            data=post_data,
            content_type='application/json'
        )
        print(post_response.data.decode('UTF-8'))
        self.assertTrue(post_response.status, 401)
        post_json = json.loads(post_response.data.decode('UTF-8'))
        print(post_json)
        self.assertTrue(post_json.get('message', False))

        post_data = json.dumps(
            {'username': 'testUserError', 'password': 'password1'}
        )
        post_response = self.app.post(
            '/api/login',
            data=post_data,
            content_type='application/json'
        )
        print(post_response)
        self.assertTrue(post_response.status, 401)
        post_json = json.loads(post_response.data.decode('UTF-8'))
        print(post_json)
        self.assertTrue(post_json.get('message', False))

        # Check that a InvalidRoleException is handled correctly.
        role = Role.from_db('demo', 'personal')
        Role.delete('demo', 'personal')
        post_data = json.dumps(
            {'username': 'testUser2', 'password': 'password2'}
        )
        post_response = self.app.post(
            '/api/login',
            data=post_data,
            content_type='application/json'
        )
        print(post_response)
        self.assertTrue(post_response.status, 500)
        post_json = json.loads(post_response.data.decode('UTF-8'))
        print(post_json)
        self.assertTrue(post_json.get('message', False))
        role.to_db()

    def test_get_user(self):
        """Test the user resource."""

        # Load user and get JWT token.
        exp = calendar.timegm(time.gmtime()) + 10
        user = User.from_db('testUser1')
        token = user.get_jwt(exp).decode('UTF-8')

        # Make a request with the jwt token in the header.
        response = self.app.post(
            '/api/get_user',
            data=json.dumps({'jwt': token}),
            content_type='application/json'
        )

        # Assemble the user that went in & the user that was taken out the func
        user_out = jwt.decode(
            json.loads(response.data.decode('UTF-8'))['jwt'],
            JWT_PUBLIC_KEY,
            algorithms=JWT_ALGORITHM
        )
        user_in = user.to_dict()

        logging.warning(user_in)
        logging.warning(user_out)

        # Check the user hasn't changed during executing the function.
        self.assertEqual(user_in['username'], user_out['usr'])
        self.assertEqual(user_in['email'], user_out['email'])
        self.assertEqual(user_in['data'], user_out['data'])
        self.assertEqual(user.get_access(), user_out['acc'])
        self.assertTrue(
            (calendar.timegm(time.gmtime()) + 10) <= user_out['exp']
        )

        # TODO: Test logout and update user.
