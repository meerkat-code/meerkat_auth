#!/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the authorise.py module in Meerkat Auth
"""
import json, meerkat_auth, unittest, jwt, calendar, time, logging, jwt, boto3, os
from datetime import datetime
from werkzeug import exceptions
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import Role, InvalidRoleException
from meerkat_auth import authorise as auth
from unittest.mock import MagicMock
from unittest import mock

#Need this module to be importable without the whole of meerkat_auth config.
#Directly load the secret settings file from which to import required variables.
#File must include JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables.
filename = os.environ.get( 'MEERKAT_AUTH_SETTINGS' )
exec( compile(open(filename, "rb").read(), filename, 'exec') )

class MeerkatAuthAuthoriseTestCase(unittest.TestCase):

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
            Role( 'demo', 'clinic', 'clinic description.', [] ),
            Role( 'demo', 'directorate', 'directorate description.', ['clinic'] ),
            Role( 'demo', 'central', 'Shared description.', ['directorate'] ),
            Role( 'jordan', 'clinic', 'Clinic description.', [] ),
            Role( 'jordan', 'directorate', 'Directorate description.', ['clinic'] ),
            Role( 'jordan', 'central', 'Central description.', ['directorate'] ),
            Role( 'jordan', 'personal', 'directorate description.', [] ),
            Role( 'jordan', 'admin', 'Backend access.', ['personal'] )
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
                ['jordan'],
                ['directorate'],
                data={
                    'name':'Testy McTestface'
                }
            ),
            User(
                'testUser2', 
                'test2@test.org.uk',
                User.hash_password('password2'),
                ['demo', 'jordan', 'jordan'],
                ['directorate', 'central', 'personal'],
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

    def test_get_token(self):
        """Test the get_token() function."""

        #get_token() looks in both the cookie headers and the authorization headers. 
        auth_headers = {'Authorization':'Bearer headertoken'}
        cookie_headers = {'Cookie':JWT_COOKIE_NAME + '=cookietoken'}

        #Check that the function responds correctly to the different types of headers.
        with meerkat_auth.app.test_request_context('/', headers = auth_headers ):
            self.assertEqual( auth.get_token(), 'headertoken' )
        with meerkat_auth.app.test_request_context('/', headers = cookie_headers ):
            self.assertEqual( auth.get_token(), 'cookietoken' )
        with meerkat_auth.app.test_request_context('/', headers = {**auth_headers, **cookie_headers} ):
            self.assertEqual( auth.get_token(), 'cookietoken' )
        with meerkat_auth.app.test_request_context('/', headers = {} ):
            self.assertEqual( auth.get_token(), '' )
        
    def test_check_access(self):
        """Test the check access function. Really important test!"""

        #testUser1 has access to a single level in a single country that inherits a single level.
        acc = User.from_db('testUser1').get_access()

        logging.warning( acc )
    
        self.assertTrue( auth.check_access( [''], [''], acc ) ) #Unrestricted access
        self.assertTrue( auth.check_access( [''], ['jordan'], acc ) ) #Unrestricted access in jordan
        self.assertTrue( auth.check_access( ['directorate'], [''], acc ) ) #Unrestricted country
        self.assertTrue( auth.check_access( ['directorate'], ['jordan'], acc ) ) #Single level
        self.assertTrue( auth.check_access( ['clinic'], ['jordan'], acc ) ) # Inherited level
        self.assertTrue( auth.check_access( ['directorate', 'admin'], ['jordan'], acc ) ) #Multiple levels
        self.assertTrue( auth.check_access( ['directorate', 'admin'], ['jordan', 'jordan'], acc ) )
        self.assertTrue( auth.check_access( ['directorate', 'clinic'], ['jordan', 'demo'], acc ) )

        self.assertFalse( auth.check_access( [''], ['demo'], acc ) ) #Unrestricted access in wrong country
        self.assertFalse( auth.check_access( ['central'], [''], acc ) ) #Parent access in any country
        self.assertFalse( auth.check_access( ['admin'], ['jordan'], acc ) ) #Single level
        self.assertFalse( auth.check_access( ['central'], ['jordan'], acc ) ) #Parent level
        self.assertFalse( auth.check_access( ['central', 'admin'], ['jordan'], acc ) ) #Multiple levels
        self.assertFalse( auth.check_access( ['central', 'admin'], ['jordan', 'jordan'], acc ) )
        self.assertFalse( auth.check_access( ['directorate', 'clinic'], ['demo', 'demo'], acc ) )

        #testUser2 has access to multiple levels across mulitple countries with multiple inherited levels.
        acc = User.from_db('testUser2').get_access()

        logging.warning( acc )
       
        self.assertTrue( auth.check_access( [''], [''], acc ) ) #Unrestricted access
        self.assertTrue( auth.check_access( [''], ['jordan'], acc ) ) #Unrestricted access in jordan
        self.assertTrue( auth.check_access( [''], ['demo'], acc ) ) #Unrestricted access in demo
        self.assertTrue( auth.check_access( ['personal'], [''], acc ) ) #Unrestricted country
        self.assertTrue( auth.check_access( ['central'], ['jordan'], acc ) ) #Single level
        self.assertTrue( auth.check_access( ['clinic'], ['jordan'], acc ) ) # Inherited level
        self.assertTrue( auth.check_access( ['root', 'directorate'], ['jordan'], acc ) ) #Multiple levels
        self.assertTrue( auth.check_access( ['root', 'clinic'], ['jordan', 'jordan'], acc ) )
        self.assertTrue( auth.check_access( ['root', 'clinic'], ['jordan', 'demo'], acc ) )

        self.assertFalse( auth.check_access( [''], ['random'], acc ) ) #Unrestricted access in wrong country
        self.assertFalse( auth.check_access( ['root'], [''], acc ) ) #Wrong access in any country
        self.assertFalse( auth.check_access( ['admin'], ['jordan'], acc ) ) #Single level
        self.assertFalse( auth.check_access( ['central'], ['demo'], acc ) ) #Parent level
        self.assertFalse( auth.check_access( ['admin', 'root'], ['jordan'], acc ) ) #Multiple levels
        self.assertFalse( auth.check_access( ['admin', 'central'], ['jordan', 'demo'], acc ) )

    def test_check_auth(self):
        """Test the check_auth function."""

        #Make a request with no token.
        with meerkat_auth.app.test_request_context('/' ):
            #Check that a 401 error is raised if no token is found where there should be one.
            self.assertRaises( 
                exceptions.Unauthorized, 
                lambda: auth.check_auth( ['directorate'], ['jordan']) 
            )
        
        #Create a token to authenticate the request.
        token = User.from_db( 'testUser1' ).get_jwt( calendar.timegm( time.gmtime() ) + 30 ).decode('UTF-8')
        auth_headers = { 'Authorization' : 'Bearer ' + token }

        #Make a request using testUser1
        with meerkat_auth.app.test_request_context('/', headers = auth_headers ):
            #Check that a 403 error is raised if trys to access page beyond users access levels.
            self.assertRaises( 
                exceptions.Forbidden, 
                lambda: auth.check_auth( ['central'], ['jordan']) 
            )   

        #Create an expired token to try and authenticate the request.
        token = User.from_db( 'testUser1' ).get_jwt( calendar.timegm( time.gmtime() ) - 1 ).decode('UTF-8')
        cookie_headers = { 'Cookie':JWT_COOKIE_NAME + "=" +token }

        #Make a request using the expired token
        with meerkat_auth.app.test_request_context('/', headers = cookie_headers ):
            #Check that a 403 error is raised if one tries to access page with expired token.
            self.assertRaises( 
                exceptions.Forbidden, 
                lambda: auth.check_auth( ['directorate'], ['jordan']) 
            )         
        
