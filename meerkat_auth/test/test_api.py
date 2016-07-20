#!/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for REST API resources in Meerkat Auth.
"""
import json, meerkat_auth, unittest, jwt, calendar, time, logging, jwt
from datetime import datetime
from meerkat_auth.util.user import User, InvalidCredentialException
from meerkat_auth.util.role import Role, InvalidRoleException

class MeerkatAuthAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_auth.app.config['TESTING'] = True
        meerkat_auth.app.config['USERS'] = 'test_auth_users'
        meerkat_auth.app.config['ROLES'] = 'test_auth_roles'
        self.app = meerkat_auth.app.test_client()

        #The database should have the following objects already in it.
        roles = [
            Role( 'demo', 'public', 'Public description.', [] ),
            Role( 'demo', 'private', 'Private description.', ['public'] ),
            Role( 'demo', 'shared', 'Shared description.', ['public'] ),
            Role( 'demo', 'manager', 'Shared description.', ['private', 'shared'] ),
            Role( 'jordan', 'public', 'Public description.', [] ),
            Role( 'jordan', 'private', 'Private description.', ['public'] )
        ]

        #Update the objects in case something else has spuriously has changed/deleted them.
        for role in roles:
            role.to_db()

        #Put into the database a couple of test users.
        users =[
            User(
                'testUser1', 
                'test1@test.org.uk',
                User.hash_password('password1'),
                ['demo', 'jordan'],
                ['manager', 'private'],
                data={
                    'name':'Testy McTestface'
                }
            ),
            User(
                'testUser2', 
                'test2@test.org.uk',
                User.hash_password('password2'),
                ['demo'],
                ['private'],
                data={
                    'name':'Tester McTestFace'
                }
            )
        ]
        for user in users:
            user.to_db()

    def tearDown(self):
        """Tear down after testing."""
        User.delete('testUser')

    def test_login(self):
        """Test the login resource."""

        #Post some data to the login function and check successful behaviour
        post_data = {'username':'testUser1', 'password':'password1'}
        post_response = self.app.post( '/login', data=post_data )
        post_json = json.loads( post_response.data.decode('UTF-8') )
        print( post_response )
        print( post_json )
        self.assertTrue( post_json.get( 'jwt', False ) )
        
        #Decode the jwt and check it is structured as expected.
        payload = jwt.decode(
            post_json['jwt'], 
            meerkat_auth.app.config['PUBLIC'], 
            algorithms=[meerkat_auth.app.config['ALGORITHM']]
        )
        print( payload )
        self.assertTrue( payload.get( 'acc', False ) )
        self.assertTrue( payload.get( 'usr', False ) )
        self.assertTrue( payload.get( 'exp', False ) )
        
        #Check the payload contents make sense.
        max_exp = calendar.timegm( time.gmtime() ) + meerkat_auth.app.config['TOKEN_LIFE']
        self.assertTrue( payload['exp'] <= max_exp )
        self.assertEquals( payload['usr'], u'testUser1' )
        expected = {
            u'demo': [u'manager', u'public', u'private', u'shared'], 
            u'jordan': [u'public', u'private']
        }
        self.assertEquals( payload['acc'], expected )

        #Now check that login fails for the wrong credentials.
        post_data = {'username':'testUser1', 'password':'password2'}
        post_response = self.app.post( '/login', data=post_data )
        print( post_response )
        self.assertTrue( post_response.status, 401 )
        post_json = json.loads( post_response.data.decode('UTF-8') )
        print( post_json )
        self.assertTrue( post_json.get( 'message', False ) )

        post_data = {'username':'testUserError', 'password':'password1'}
        post_response = self.app.post( '/login', data=post_data )
        print( post_response )
        self.assertTrue( post_response.status, 401 )
        post_json = json.loads( post_response.data.decode('UTF-8') )
        print( post_json )
        self.assertTrue( post_json.get( 'message', False ) )

        #Check that a InvalidRoleException is handled correctly.
        role=Role.from_db('demo','private')
        Role.delete('demo','private')
        post_data = {'username':'testUser2', 'password':'password2'}
        post_response = self.app.post( '/login', data=post_data )
        print( post_response )
        self.assertTrue( post_response.status, 500 )
        post_json = json.loads( post_response.data.decode('UTF-8') )
        print( post_json )
        self.assertTrue( post_json.get( 'message', False ) )    
        role.to_db()

    def test_get_user(self):
        """Test the user resource."""

        #Load user and get JWT token.
        exp =calendar.timegm( time.gmtime() ) + 10
        token = User.from_db('testUser1').get_jwt(exp)
        headers = {
            'Authorization': 'Bearer ' + token
        }
        #Make a request with the jwt token in the header.
        response = self.app.get( '/user', headers=headers)
        
