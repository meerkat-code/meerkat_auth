#!/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for REST API resources in Meerkat Auth.
"""
import json, meerkat_auth, unittest, jwt, calendar, time, logging, jwt, boto3, os
from datetime import datetime
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import Role, InvalidRoleException
from unittest.mock import MagicMock
from unittest import mock

#Need this module to be importable without the whole of meerkat_auth config.
#Directly load the secret settings file from which to import required variables.
#File must include JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables.
filename = os.environ.get( 'MEERKAT_AUTH_SETTINGS' )
exec( compile(open(filename, "rb").read(), filename, 'exec') )

class MeerkatAuthAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_auth.app.config['TESTING'] = True
        meerkat_auth.app.config['USERS'] = 'test_auth_users'
        meerkat_auth.app.config['ROLES'] = 'test_auth_roles'
        meerkat_auth.app.config['DB_URL'] = 'https://dynamodb.eu-west-1.amazonaws.com'
        User.DB= boto3.resource(
            'dynamodb', 
            endpoint_url="https://dynamodb.eu-west-1.amazonaws.com", 
            region_name='eu-west-1'
        )
        Role.DB= boto3.resource(
            'dynamodb', 
            endpoint_url="https://dynamodb.eu-west-1.amazonaws.com", 
            region_name='eu-west-1'
        )
        self.app = meerkat_auth.app.test_client()
        logging.warning( meerkat_auth.app.config['DB_URL'] )
        #The database should have the following objects already in it.
        roles = [
            Role( 'demo', 'registered', 'Registered description.', [] ),
            Role( 'demo', 'personal', 'Personal description.', ['registered'] ),
            Role( 'demo', 'shared', 'Shared description.', ['registered'] ),
            Role( 'demo', 'manager', 'Shared description.', ['personal', 'shared'] ),
            Role( 'jordan', 'registered', 'Registered description.', [] ),
            Role( 'jordan', 'personal', 'Personal description.', ['registered'] )
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
                ['manager', 'personal'],
                data={
                    'name':'Testy McTestface'
                }
            ),
            User(
                'testUser2', 
                'test2@test.org.uk',
                User.hash_password('password2'),
                ['demo'],
                ['personal'],
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

    @mock.patch('flask.Response.set_cookie')
    def test_login(self, request_mock):
        """Test the login resource."""

        #Post some data to the login function and check successful behaviour
        post_data = json.dumps({'username':'testUser1', 'password':'password1'})
        post_response = self.app.post( '/api/login', data=post_data, content_type='application/json')
        post_json = json.loads( post_response.data.decode('UTF-8') )
        response_jwt = request_mock.call_args[1]['value'].decode('UTF-8')

        self.assertEqual( post_json.get( 'message', '' ), 'successful' )
        self.assertTrue( request_mock.called )
        
        #Decode the jwt and check it is structured as expected.
        payload = jwt.decode(
            response_jwt, 
            JWT_PUBLIC_KEY, 
            algorithms=JWT_ALGORITHM
        )
        self.assertTrue( payload.get( 'acc', False ) )
        self.assertTrue( payload.get( 'usr', False ) )
        self.assertTrue( payload.get( 'exp', False ) )
        
        #Check the payload contents make sense.
        max_exp = calendar.timegm( time.gmtime() ) + meerkat_auth.app.config['TOKEN_LIFE']
        self.assertTrue( payload['exp'] <= max_exp )
        self.assertEquals( payload['usr'], u'testUser1' )
        expected = {
            u'demo': [u'manager', u'registered', u'personal', u'shared'], 
            u'jordan': [u'registered', u'personal']
        }
        for key in expected.keys():
            self.assertEqual( set(expected[key]), set(payload['acc'][key]) )

        #Now check that login fails for the wrong credentials.
        post_data = json.dumps({'username':'testUser1', 'password':'password2'})
        post_response = self.app.post( '/api/login', data=post_data, content_type='application/json' )
        print( post_response.data.decode('UTF-8') )
        self.assertTrue( post_response.status, 401 )
        post_json = json.loads( post_response.data.decode('UTF-8') )
        print( post_json )
        self.assertTrue( post_json.get( 'message', False ) )

        post_data = json.dumps({'username':'testUserError', 'password':'password1'})
        post_response = self.app.post( '/api/login', data=post_data, content_type='application/json' )
        print( post_response )
        self.assertTrue( post_response.status, 401 )
        post_json = json.loads( post_response.data.decode('UTF-8') )
        print( post_json )
        self.assertTrue( post_json.get( 'message', False ) )

        #Check that a InvalidRoleException is handled correctly.
        role=Role.from_db('demo','personal')
        Role.delete('demo','personal')
        post_data = json.dumps({'username':'testUser2', 'password':'password2'})
        post_response = self.app.post( '/api/login', data=post_data, content_type='application/json' )
        print( post_response )
        self.assertTrue( post_response.status, 500 )
        post_json = json.loads( post_response.data.decode('UTF-8') )
        print( post_json )
        self.assertTrue( post_json.get( 'message', False ) )    
        role.to_db()

# THIS ISN'T REQUIRED YET
#    def test_get_user(self):
#        """Test the user resource."""
#
#        #Load user and get JWT token.
#        exp =calendar.timegm( time.gmtime() ) + 10
#        token = User.from_db('testUser1').get_jwt(exp).decode('UTF-8')
#        headers = {
#            'Authorization': 'Bearer ' + token
#        }
#
#        #Make a request with the jwt token in the header.
#        response = self.app.get( '/api/get_user', headers=headers)
#        logging.warning( response.data.decode('UTF-8') )
#        user_out = json.loads( response.data.decode('UTF-8') )
#        user_in = User.from_db('testUser1').to_dict()    
#        
#        #Assert that the user returned equals the user put into the database.
#        for key in user_in:
#            matched = user_in[key] == user_out[key] 
#            if not matched:
#                logging.warning( "Key '" + key + "' not matched." )           
#            self.assertTrue( matched )

    #TODO: Properly test the require_jwt decorator and check_access functions.

        
