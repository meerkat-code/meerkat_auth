# !/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the utility class User in Meerkat Auth.
"""

from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import InvalidRoleException
from meerkat_auth import app
from meerkat_libs import db_adapters
from unittest import mock
import unittest
import jwt
import calendar
import time
import os
import importlib.util

# Load the secret settings module where the JWT details are stored.
filename = os.environ.get('MEERKAT_AUTH_SETTINGS')
spec = importlib.util.spec_from_file_location("settings", filename)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class MeerkatAuthUserTestCase(unittest.TestCase):

    maxDiff = None

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

    def test_to_db(self):
        """Test the user to_db() method"""
        user = {
            'username': 'testUser',
            'email': 'test@test.org.uk',
            'password': ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            'countries': ['demo', 'jordan'],
            'roles': ['manager', 'personal'],
            'data': {'name': 'Testy McTestface'},
            'state': 'new',
        }

        expected_attributes = {**user.copy(), **{
            'state': 'live',
            'creation': mock.ANY,
            'updated': mock.ANY
        }}
        del expected_attributes['username']

        User(**user).to_db()
        app.db.write.assert_called_with(
            app.config['USERS'],
            {'username': user['username']},
            expected_attributes
        )

    def test_from_db(self):
        """Test the user from_db() method"""
        user = {
            'username': 'testUser',
            'email': 'test@test.org.uk',
            'password': ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            'countries': ['demo', 'jordan'],
            'roles': ['manager', 'personal'],
            'data': {'name': 'Testy McTestface'},
            'state': 'new',
        }
        self.db_data[app.config['USERS']]['username:'+user['username']] = user
        output = User.from_db(user['username'])
        expected_calls = [
            mock.call(app.config['USERS'], {'username': 'testUser'}),
            mock.call(app.config['ROLES'], {'country': 'demo', 'role': 'manager'}),
            mock.call(app.config['ROLES'], {'country': 'jordan', 'role': 'personal'})
        ]
        app.db.read.assert_has_calls(expected_calls)
        self.assertEqual(User(**user), output)
        self.assertRaises(
            InvalidCredentialException,
            lambda: User.from_db('nonexistant')
        )

    def test_delete(self):
        """Test the user delete() method"""
        user = {
            'username': 'testUser',
            'email': 'test@test.org.uk',
            'password': ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            'countries': ['demo', 'jordan'],
            'roles': ['manager', 'personal'],
            'data': {'name': 'Testy McTestface'},
            'state': 'new'
        }
        self.db_data[app.config['USERS']]['username:'+user['username']] = user

        User.delete(user['username'])
        app.db.delete.assert_called_with(
            app.config['USERS'],
            {'username': user['username']}
        )

    def test_get_access(self):
        """Test the user get_access() method"""

        # Create the test user.
        user = User(
            'testUser',
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name': 'Testy McTestface'
            }
        )
        access = user.get_access()

        # Check that the expected access has been returned.
        demo_expected = ['manager', 'personal', 'shared', 'registered']
        jordan_expected = ['personal', 'registered']
        self.assertEquals(len(access), 2)
        self.assertTrue('jordan' in access)
        self.assertTrue('demo' in access)
        self.assertTrue(set(demo_expected) == set(access['demo']))
        self.assertTrue(set(jordan_expected) == set(access['jordan']))

        # Check that get_access breaks appropriately if the roles are wrong.
        del self.db_data[app.config['ROLES']]['country:demo-role:registered']
        self.assertRaises(InvalidRoleException, lambda: user.get_access())

    def test_get_jwt(self):
        """Test the user get_jwt() method"""

        # Create the test user.
        user = User(
            'testUser',
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name': 'Testy McTestface'
            }
        )
        # Create JWT from the test user with a very short lifetime (1 second)
        exp = calendar.timegm(time.gmtime()) + 1

        user_encoded = user.get_user_jwt(exp)
        encoded = user.get_jwt(exp)

        # Decode the JWT and check it is as expected.
        decoded = jwt.decode(
            encoded,
            settings.JWT_PUBLIC_KEY,
            settings.JWT_ALGORITHM
        )
        user_decoded = jwt.decode(
            user_encoded,
            settings.JWT_PUBLIC_KEY,
            settings.JWT_ALGORITHM
        )

        user_expected = {
            u'acc': {
                u'demo': [u'manager', u'registered', u'shared', u'personal'],
                u'jordan': [u'registered', u'personal']
            },
            u'data': {u'name': u'Testy McTestface'},
            u'usr': u'testUser',
            u'exp': exp,
            u'email': u'test@test.org.uk'
        }
        expected = {
            u'usr': u'testUser',
            u'exp': exp,
        }

        # Compare access lists. Note: order od dict isn't predictable.
        decoded_acc = user_decoded.pop('acc', None)
        expected_acc = user_expected.pop('acc', None)
        for key in expected_acc.keys():
            self.assertEqual(set(expected_acc[key]), set(decoded_acc[key]))

        # Check the rest of the tokens are equal.
        decoded.pop('acc', None)
        self.assertEqual(expected, decoded)
        self.assertEqual(user_expected, user_decoded)

        # Let the computer sleep through the liftime of the JWT.
        time.sleep(2)

        # Check that decoding JWT doesn't complain with ExpiredSignatureError.
        self.assertRaises(jwt.ExpiredSignatureError, lambda: jwt.decode(
            encoded,
            settings.JWT_PUBLIC_KEY,
            settings.JWT_ALGORITHM
        ))
        self.assertRaises(jwt.ExpiredSignatureError, lambda: jwt.decode(
            user_encoded,
            settings.JWT_PUBLIC_KEY,
            settings.JWT_ALGORITHM
        ))

    def test_validate_user(self):
        """Test the user validation"""

        # Check that a valid set of arguments passes the validation function.
        try:
            User(
                'testUser',
                'test@test.org.uk',
                User.hash_password('password'),
                ['demo', 'jordan'],
                ['manager', 'personal'],
                state='new'
            ).validate()
        except InvalidCredentialException as e:
            self.fail(repr(e))
        except InvalidRoleException as e:
            self.fail(repr(e))

        # Check that bad arguments raises the correct exceptions
        self.assertRaises(
            InvalidCredentialException,
            lambda: User(
                'testUser',
                'testtest.org.uk',
                User.hash_password('password'),
                ['demo', 'jordan'],
                ['manager', 'personal'],
                state='new'
            ).validate()
        )
        self.assertRaises(
            InvalidRoleException,
            lambda: User(
                'testUser',
                'test@test.org.uk',
                User.hash_password('password'),
                ['demo', 'jordan'],
                ['superroot', 'personal'],
                state='new'
            ).validate()
        )
        self.assertRaises(
            InvalidRoleException,
            lambda: User(
                'testUser',
                'test@test.org.uk',
                User.hash_password('password'),
                ['neverland', 'jordan'],
                ['manager', 'personal'],
                state='new'
            ).validate()
        )

        # Create and write to db a valid user with the same username.
        # Check that the username is then invalid for new user creation.
        user = User(
            'testUser',
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name': 'Testy McTestface'
            },
            state='new'
        )
        user.to_db()

        # Edit the user badly and check it's picked up by validate()
        user.password = 'password'
        self.assertRaises(InvalidCredentialException, lambda: user.to_db())

        user.password = ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
                         'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y')
        user.email = 'not@anemailaddress'
        self.assertRaises(InvalidCredentialException, lambda: user.to_db())

        user.email = 'test@test.com'
        user.countries = ['neverland', 'jordan']
        self.assertRaises(InvalidRoleException, lambda: user.to_db())

        user.countries = ['demo', 'jordan']
        user.username = 'notindb'
        self.assertRaises(InvalidCredentialException, lambda: user.to_db())

        user.state = 'new'
        try:
            user.validate()
        except InvalidCredentialException as e:
            self.fail(repr(e))

    def test_authenticate(self):
        """Test the user authenticate() method"""

        # Create a test user and write to db.
        user = User(
            'testUser',
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name': 'Testy McTestface'
            },
            state='new'
        )
        user.to_db()

        # Check that we can authenticate successfully.
        try:
            user = User.authenticate('testUser', 'password')
            self.assertTrue(isinstance(user, User))
        except InvalidCredentialException as e:
            self.fail(repr(e))

        # Check that authentication fails for wrong details.
        self.assertRaises(
            InvalidCredentialException,
            lambda: User.authenticate('testUser', 'wrongpass')
        )
        self.assertRaises(
            InvalidCredentialException,
            lambda: User.authenticate('wronguser', 'password')
        )

    def test_get_all(self):
        """Test the user get_all() method"""
        # Check call when falsy conds and attrs supplied
        User.get_all([], [])
        app.db.get_all.assert_called_with(
            app.config['USERS'],
            {'countries': []},
            []
        )
        # Check call when non-lists provided
        User.get_all('jordan', 'email')
        app.db.get_all.assert_called_with(
            app.config['USERS'],
            {'countries': ['jordan']},
            ['email', 'username']
        )
        # Check call when username not provided
        User.get_all(['jordan', 'demo'], ['email', 'roles'])
        app.db.get_all.assert_called_with(
            app.config['USERS'],
            {'countries': ['jordan', 'demo']},
            ['email', 'roles', 'username']
        )
