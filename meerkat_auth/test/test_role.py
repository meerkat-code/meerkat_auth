#!/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the utility class role in Meerkat Auth.
"""
import json, unittest, meerkat_auth
from datetime import datetime
from meerkat_auth.util.role import Role, InvalidRoleException

class MeerkatAuthRoleTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_auth.app.config['TESTING'] = True
        meerkat_auth.app.config['USERS'] = 'test_auth_users'
        meerkat_auth.app.config['ROLES'] = 'test_auth_roles'
        
    def tearDown(self):
        """Tear down after testing."""
        pass

    def test_io(self):
        """Test the Role class' database writing/reading/deleting functions."""
        
        #Create a test role object.
        role1 = Role(
            'demo', 
            'testRole',
            'Test role description.',
            ['private']
        )
        print( 'role1:\n' + repr(role1) )

        #Put the role into the database and take it out again.
        role1.to_db()
        role2 = Role.from_db('demo','testRole')
        print( 'role2:\n' + repr(role1) )

        #Check that the role out of the database equals the role that went in.
        self.assertEqual( role1.country, role2.country )
        self.assertEqual( role1.role, role2.role ) 
        self.assertEqual( role1.description, role2.description )
        self.assertEqual( role1.parents, role2.parents )

        #Check that the role can be deleted and then from_db() raises exception.
        Role.delete( role1.country, role1.role )
        self.assertRaises( Exception, lambda: Role.from_db( role1.country, role1.role ) )

    def test_all_parents(self):
        """Test the Role class private method all_access_objs()."""
        #The database should have the following objects already in it.
        roles = {
            'registered': Role( 'demo', 'registered', 'Registered description.', [] ),
            'private': Role( 'demo', 'private', 'Private description.', ['registered'] ),
            'shared': Role( 'demo', 'shared', 'Shared description.', ['registered'] ),
            'manager': Role( 'demo', 'manager', 'Shared description.', ['private', 'shared'] )
        }
        #Update the objects in case something has changed them.
        for role in roles:
            roles[role].to_db()

        #Get all the manager parents.
        parents = roles['manager'].all_access()
        #Check the correct list is returned
        print( "Manager parents: " + str( parents ) )
        self.assertEqual( len(parents), 4 )
        self.assertIn( 'registered', parents )
        self.assertIn( 'private', parents )
        self.assertIn( 'shared', parents )
        self.assertIn( 'manager', parents )

        #Get all the private parents.
        parents = roles['private'].all_access()
        #Check the correct list is returned
        print( "private parents: " + str( parents ) )
        self.assertEqual( len(parents), 2 )
        self.assertIn( 'registered', parents )
        self.assertIn( 'private', parents )

        #Get all the registered parents.
        parents = roles['registered'].all_access()
        #Check the correct list is returned
        print( "Registered parents: " + str( parents ) )
        self.assertEqual( len(parents), 1 )
        self.assertIn( 'registered', parents )

    def test_validate(self):
        """Test the Role validate functions."""
        #The database should have the following objects already in it.
        roles = {
            'registered': 
                Role( 'demo', 'registered', 'Registered description.', [] ),
            'private': 
                Role( 'demo', 'private', 'Private description.', ['registered'] ),
            'shared': 
                Role( 'demo', 'shared', 'Shared description.', ['registered'] ),
            'manager': 
                Role( 'demo', 'manager', 'Shared description.', ['private', 'shared'] )
        }
        #Update the objects in case something has changed them.
        for role in roles:
            roles[role].to_db()        
        
        #Check that a valid role passes the validate check.
        try:        
            Role.validate_role( 'demo', 'manager' )
            roles['manager'].validate()
        except InvalidRoleException as e:
            self.fail( repr(e) )
        
        #Check that breaking the ancestor tree breaks the validation.
        Role.delete( 'demo', 'shared' )
        self.assertRaises( 
            InvalidRoleException, lambda: Role.validate_role( 'demo', 'manager' )
        )
        self.assertRaises( 
            InvalidRoleException, lambda: roles['manager'].validate()
        )


