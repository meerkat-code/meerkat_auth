# !/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the utility class role in Meerkat Auth.
"""

from meerkat_auth.role import Role, InvalidRoleException
from meerkat_auth import app

import unittest
import boto3


class MeerkatAuthRoleTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        app.config['TESTING'] = True
        app.config['USERS'] = 'test_auth_users'
        app.config['ROLES'] = 'test_auth_roles'
        app.config['DB_URL'] = 'https://dynamodb.eu-west-1.amazonaws.com'
        Role.DB = boto3.resource(
            'dynamodb',
            endpoint_url="https://dynamodb.eu-west-1.amazonaws.com",
            region_name='eu-west-1'
        )
        # Put some roles into the test db.
        roles = [
            Role('demo', 'registered', 'Registered.', []),
            Role('demo', 'personal', 'Personal.', ['registered']),
            Role('demo', 'shared', 'Shared.', ['registered']),
            Role('demo', 'manager', 'Manager.', ['personal', 'shared']),
            Role('jordan', 'registered', 'Registered.', []),
            Role('jordan', 'personal', 'Personal.', ['registered'])
        ]
        for role in roles:
            role.to_db()

        # Store roles indexed in a manner  helpful for reference in the tests.
        self.demo_roles = {}
        self.jordan_roles = {}
        for role in roles:
            if role.country == 'demo':
                self.demo_roles[role.role] = role
            elif role.country == 'jordan':
                self.jordan_roles = role

    def tearDown(self):
        """Tear down after testing."""
        # Delete the roles in the database after finishing the tests.
        table = Role.DB.Table(app.config['ROLES'])
        response = table.scan()
        with table.batch_writer() as batch:
            for role in response.get('Items', []):
                batch.delete_item(
                    Key={
                        'country': role['country'],
                        'role': role['role']
                    }
                )

    def test_io(self):
        """Test the Role class' database writing/reading/deleting functions."""

        # Create a test role object.
        role1 = Role(
            'demo',
            'testRole',
            'Test role description.',
            ['personal']
        )
        print('role1:\n' + repr(role1))

        # Put the role into the database and take it out again.
        role1.to_db()
        role2 = Role.from_db('demo', 'testRole')
        print('role2:\n' + repr(role1))

        # Check that the role out of the database equals the role that went in.
        self.assertEqual(role1.country, role2.country)
        self.assertEqual(role1.role, role2.role)
        self.assertEqual(role1.description, role2.description)
        self.assertEqual(role1.parents, role2.parents)

        # Check the role can be deleted and then from_db() raises exception.
        Role.delete(role1.country, role1.role)
        self.assertRaises(
            Exception,
            lambda: Role.from_db(role1.country, role1.role)
        )

    def test_all_parents(self):
        """Test the Role class private method all_access_objs()."""

        roles = self.demo_roles

        # Get all the manager parents.
        parents = roles['manager'].all_access()
        # Check the correct list is returned
        print("Manager parents: " + str(parents))
        self.assertEqual(len(parents), 4)
        self.assertIn('registered', parents)
        self.assertIn('personal', parents)
        self.assertIn('shared', parents)
        self.assertIn('manager', parents)

        # Get all the private parents.
        parents = roles['personal'].all_access()
        # Check the correct list is returned
        print("private parents: " + str(parents))
        self.assertEqual(len(parents), 2)
        self.assertIn('registered', parents)
        self.assertIn('personal', parents)

        # Get all the registered parents.
        parents = roles['registered'].all_access()
        # Check the correct list is returned
        print("Registered parents: " + str(parents))
        self.assertEqual(len(parents), 1)
        self.assertIn('registered', parents)

    def test_validate(self):
        """Test the Role validate functions."""

        roles = self.demo_roles

        # Check that a valid role passes the validate check.
        try:
            Role.validate_role('demo', 'manager')
            roles['manager'].validate()
        except InvalidRoleException as e:
            self.fail(repr(e))

        # Check that breaking the ancestor tree breaks the validation.
        Role.delete('demo', 'shared')
        self.assertRaises(
            InvalidRoleException, lambda: Role.validate_role('demo', 'manager')
        )
        self.assertRaises(
            InvalidRoleException, lambda: roles['manager'].validate()
        )

    def test_get_all(self):
        """Test the staticmethod get_all()."""

        # Request just roles from demo.
        response = Role.get_all('demo')
        self.assertEqual(len(response), 4)

        # Request just roles from jordan.
        response = Role.get_all(['jordan'])
        self.assertEqual(len(response), 2)

        # Request all roles.
        response = Role.get_all(None)
        self.assertEqual(len(response), 6)

        # Request all roles.
        response = Role.get_all(['demo', 'jordan'])
        self.assertEqual(len(response), 6)
