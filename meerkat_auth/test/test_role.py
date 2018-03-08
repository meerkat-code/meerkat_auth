# !/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the utility class role in Meerkat Auth.
"""

from meerkat_auth.role import Role, InvalidRoleException
from meerkat_auth import app, db_adapters
from unittest import mock
import unittest


class MeerkatAuthRoleTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        app.config.from_object('meerkat_auth.config.Testing')
        app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
        app.db = mock.create_autospec(db_adapters.DynamoDBAdapter)
        self.roles = {
            'registered': {
                'country': 'demo', 'role': 'registered',
                'description': 'Registered.', 'parents': []
            },
            'personal': {
                'country': 'demo', 'role': 'personal',
                'description': 'Personal.', 'parents': ['registered']
            },
            'shared': {
                'country': 'demo', 'role': 'shared',
                'description': 'Shared.', 'parents': ['registered']
            },
            'manager': {
                'country': 'demo', 'role': 'manager',
                'description': 'Manager.', 'parents': ['personal', 'shared']
            },
            'testrole': {
                'country': 'demo', 'role': 'testrole', 'visible': ['manager'],
                'description': 'Manager.', 'parents': []
            }
        }

    def test_to_db(self):
        """Test the role to_db() method"""
        role = self.roles['testrole']
        Role(**role).to_db()
        app.db.write.assert_called_with(
            app.config['ROLES'],
            {'country': role['country'], 'role': role['role']},
            {'description': role['description'],
             'parents': role['parents'],
             'visible': role['visible']}
        )

    def test_from_db(self):
        """Test the role from_db() method"""
        role = self.roles['testrole']
        app.db.read.side_effect = [role]
        output = Role.from_db(role['country'], role['role'])
        app.db.read.assert_called_with(
            app.config['ROLES'],
            {'country': role['country'], 'role': role['role']}
        )
        self.assertEqual(Role(**role), output)
        app.db.read.side_effect = [None]  # Raises InvalidRole Exception properly.
        self.assertRaises(
            InvalidRoleException,
            lambda: Role.from_db(role['country'], role['role'])
        )

    def test_delete(self):
        """Test the role delete() method"""
        role = self.roles['testrole']
        Role.delete(role['country'], role['role'])
        app.db.delete.assert_called_with(
            app.config['ROLES'],
            {'country': role['country'], 'role': role['role']}
        )

    def test_get_all(self):
        """Test the role get_all() method"""
        roles = list(self.roles.values())
        app.db.get_all.side_effect = [roles, roles]
        response = Role.get_all('demo')
        app.db.get_all.assert_called_with(
            app.config['ROLES'],
            {'countries': ['demo']}
        )
        for input_role, output_role in zip(roles, response):
            self.assertDictEqual(input_role, output_role)
        response = Role.get_all(None)
        app.db.get_all.assert_called_with(
            app.config['ROLES'],
            {'countries': []}
        )

    def test_all_parents(self):
        """Test the role all_access_objs() method."""

        roles = self.roles

        def side_effect(table, key):
            app.logger.warning(key['role'])
            return roles.get(key['role'], None)

        app.db.read.side_effect = side_effect

        # Get all the manager parents.
        parents = Role(**roles['manager']).all_access()
        # Check the correct list is returned
        print("Manager parents: " + str(parents))
        self.assertEqual(len(parents), 4)
        self.assertIn('registered', parents)
        self.assertIn('personal', parents)
        self.assertIn('shared', parents)
        self.assertIn('manager', parents)

        # Get all the private parents.
        parents = Role(**roles['personal']).all_access()
        # Check the correct list is returned
        print("private parents: " + str(parents))
        self.assertEqual(len(parents), 2)
        self.assertIn('registered', parents)
        self.assertIn('personal', parents)

        # Get all the registered parents.
        parents = Role(**roles['registered']).all_access()
        # Check the correct list is returned
        print("Registered parents: " + str(parents))
        self.assertEqual(len(parents), 1)
        self.assertIn('registered', parents)

    def test_validate(self):
        """Test the role validate functions."""
        roles = self.roles

        def side_effect(table, key):
            app.logger.warning(key['role'])
            return roles.get(key['role'], None)

        app.db.read.side_effect = side_effect

        # Check that a valid role passes the validate check.
        try:
            Role.validate_role('demo', 'manager')
            Role(**roles['manager']).validate()
        except InvalidRoleException as e:
            self.fail(repr(e))

        # Check that breaking the ancestor tree breaks the validation.
        del roles['shared']
        self.assertRaises(
            InvalidRoleException, lambda: Role.validate_role('demo', 'manager')
        )
        self.assertRaises(
            InvalidRoleException, lambda: Role(**roles['manager']).validate()
        )
