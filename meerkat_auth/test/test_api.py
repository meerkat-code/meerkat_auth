# !/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for REST API resources in Meerkat Auth.
"""
from meerkat_auth.user import User
from meerkat_auth.role import Role
from unittest import mock
from meerkat_auth import app, db_adapters
import meerkat_auth
import json
import unittest
import jwt
import calendar
import time
import logging


class MeerkatAuthAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        app.config.from_object('meerkat_auth.config.Testing')
        app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
        self.app = meerkat_auth.app.test_client()

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
        app.db.delete.side_effect = read_effect

        # Initialise the db
        roles = [
            {'country': 'demo', 'role': 'registered',
             'description': 'Registered.', 'parents': []},
            {'country': 'demo', 'role': 'personal',
             'description': 'Personal.', 'parents': ['registered']},
            {'country': 'demo', 'role': 'shared',
             'description': 'Shared.', 'parents': ['registered']},
            {'country': 'demo', 'role': 'manager',
             'description': 'Manager.', 'parents': ['personal', 'shared']},
            {'country': 'jordan', 'role': 'registered',
             'description': 'Registered.', 'parents': []},
            {'country': 'jordan', 'role': 'personal',
             'description': 'Personal.', 'parents': ['registered']}
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
             'countries': ['demo', 'jordan'],
             'roles': ['manager', 'personal'],
             'data': {'name': 'Testy McTestface'}},
            {'username': 'testUser2',
             'email': 'test2@test.org.uk',
             'password': User.hash_password('password2'),
             'countries': ['demo', 'jordan'],
             'roles': ['manager', 'personal'],
             'data': {'name': 'Tester McTestface'}}
        ]

        for user in users:
            keys = {'username': user['username']}
            write_effect(
                app.config['USERS'],
                keys,
                {k: user[k] for k in user if k not in keys}
            )

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
            app.config['JWT_PUBLIC_KEY'],
            algorithms=app.config['JWT_ALGORITHM']
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
            app.config['JWT_PUBLIC_KEY'],
            algorithms=app.config['JWT_ALGORITHM']
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
