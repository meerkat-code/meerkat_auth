#!/usr/bin/env python3
"""
Meerkat Auth Tests

Unit tests for the utility class User in Meerkat Auth.
"""
import json, meerkat_auth, unittest, jwt, calendar, time, logging, boto3, os
from datetime import datetime
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import Role, InvalidRoleException

#Need this module to be importable without the whole of meerkat_auth config.
#Directly load the secret settings file from which to import required variables.
#File must include JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables.
filename = os.environ.get( 'MEERKAT_AUTH_SETTINGS' )
exec( compile(open(filename, "rb").read(), filename, 'exec') )

class MeerkatAuthUserTestCase(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        """Setup for testing"""
        meerkat_auth.app.config['TESTING'] = True
        meerkat_auth.app.config['USERS'] = 'test_auth_users'
        meerkat_auth.app.config['ROLES'] = 'test_auth_roles'
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

    def tearDown(self):
        """Tear down after testing."""
        User.delete('testUser')

    def test_io(self):
        """Test the User class' database writing/reading/deleting functions."""
        user1 = User(
            'testUser', 
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name':'Testy McTestface'
            },
            state='new'
        )
        print( 'User1:\n' + repr(user1) )

        #Put the user into the database and then fetch it again.
        user1.to_db()
        user2 = User.from_db(user1.username)
        print( 'User2:\n' + repr(user2) )

        #Check no alterations have taken place in the above process.
        self.assertEqual( user1.username, user2.username )
        self.assertEqual( user1.email, user2.email ) 
        self.assertEqual( user1.password, user2.password )
        self.assertEqual( user1.countries, user2.countries )
        self.assertEqual( user1.roles, user2.roles )
        self.assertEqual( user1.data, user2.data)
        self.assertEqual( len(user1.role_objs), len(user2.role_objs) )

        #Check that the user can be deleted and then from_db() raises exception.
        User.delete( user1.username )
        self.assertRaises( InvalidCredentialException, lambda: User.from_db( user1.username ) )

    def test_get_access(self):
        """Tests the get_access() method of User objects."""

        #Create the test user.
        user = User(
            'testUser', 
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name':'Testy McTestface'
            }
        )
        access = user.get_access()

        #Check that the expected access has been returned.
        print( access )
        demo_expected = ['manager','personal','shared','registered']
        jordan_expected = ['personal','registered']
        self.assertEquals( len(access), 2 ) 
        self.assertTrue( 'jordan' in access )
        self.assertTrue( 'demo' in access )
        self.assertTrue( set(demo_expected) == set(access['demo']) )
        self.assertTrue( set(jordan_expected) == set(access['jordan']) )

        #Check that get_access breaks appropriately if the roles are wrong.
        demo_registered = Role.from_db( 'demo','registered' )
        print(Role.delete( 'demo', 'registered' ))
        self.assertRaises( InvalidRoleException, lambda: user.get_access() )
        demo_registered.to_db()
        
    def test_get_jwt(self):
        """Tests the get_jwt() method of User objects."""

        #Create the test user.
        user = User(
            'testUser', 
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name':'Testy McTestface'
            }
        )
        #Create JWT from the test user with a very short lifetime (1 second)
        exp = calendar.timegm( time.gmtime() ) + 1
   
        user_encoded = user.get_user_jwt(exp)
        encoded = user.get_jwt(exp)
        
        #Decode the JWT and check it is as expected.
        decoded = jwt.decode(
            encoded, 
            JWT_PUBLIC_KEY, 
            JWT_ALGORITHM
        )
        user_decoded = jwt.decode(
            user_encoded, 
            JWT_PUBLIC_KEY, 
            JWT_ALGORITHM
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
            u'usr':u'testUser',
            u'exp': exp
        }

        #Extract the access lists and compare seperately because their order isn't predictable.
        decoded_acc = user_decoded.pop('acc', None )
        expected_acc = user_expected.pop( 'acc', None )
        for key in expected_acc.keys():
            self.assertEqual( set(expected_acc[key]), set( decoded_acc[key] ) )

        #Check the rest of the tokens are equal.
        self.assertEqual(expected, decoded)
        self.assertEqual(user_expected, user_decoded)
        
        #Let the computer sleep through the liftime of the JWT. 
        time.sleep(2)

        #Check that decoding the JWT not complains with an ExpiredSignatureError
        self.assertRaises( jwt.ExpiredSignatureError, lambda: jwt.decode(
            encoded, 
            JWT_PUBLIC_KEY, 
            JWT_ALGORITHM
        ))
        self.assertRaises( jwt.ExpiredSignatureError, lambda: jwt.decode(
            user_encoded, 
            JWT_PUBLIC_KEY, 
            JWT_ALGORITHM
        ))

    def test_validate_user(self):
        """Tests the validation of user details."""

        #Check that a valid set of arguments passes the validation function.
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
            self.fail( repr(e) ) 
        except InvalidRoleException as e:
            self.fail( repr(e) )
        
        #Check that bad arguments raises the correct exceptions
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
        
        #Create and write to db a valid user with the same username. 
        #Check that the username is then invalid for new user creation.
        user = User(
            'testUser', 
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'),
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name':'Testy McTestface'
            },
            state='new'
        )    
        user.to_db()
        
        #Edit the user badly and check it's picked up by validate()
        user.password = 'password'
        self.assertRaises( InvalidCredentialException, lambda: user.to_db() )

        user.password = ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
            'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y')
        user.email = 'not@anemailaddress'
        self.assertRaises( InvalidCredentialException, lambda: user.to_db() )

        user.email = 'test@test.com'
        user.countries = ['neverland', 'jordan']
        self.assertRaises( InvalidRoleException, lambda: user.to_db() )

        user.countries = ['demo', 'jordan']
        user.username = 'notindb'
        self.assertRaises( InvalidCredentialException, lambda: user.to_db()  )

        user.state = 'new'
        try:
            user.validate()
        except InvalidCredentialException as e:
            self.fail( repr(e) )

        #Clean up
        User.delete( 'testUser' )

    def test_authenticate(self):
        """Test the authenticate method."""

        #Create a test user and write to db.
        user = User(
            'testUser', 
            'test@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'), #Hash of 'password'
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name':'Testy McTestface'
            },
            state='new'
        )    
        user.to_db()
        
        #Check that we can authenticate successfully.
        try:
            user = User.authenticate( 'testUser', 'password' )
            self.assertTrue( isinstance( user, User ) )
        except InvalidCredentialException as e:
            self.fail( repr(e) )

        #Check that authentication fails for wrong details.
        self.assertRaises(
            InvalidCredentialException, 
            lambda: User.authenticate( 'testUser', 'wrongpass' )
        )
        self.assertRaises( 
            InvalidCredentialException,
            lambda: User.authenticate( 'wronguser', 'password' ) 
        )

    def test_get_all(self):
        """Test the staticmethod get_all()."""
        #Create the test users.
        #Create a test user and write to db.
        user1 = User(
            'testUser1', 
            'test1@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'), #Hash of 'password'
            ['demo', 'jordan'],
            ['manager', 'personal'],
            data={
                'name':'Testy McTestface'
            },
            state='live'
        )    
        user1.to_db()

        user2 = User(
            'testUser2', 
            'test2@test.org.uk',
            ('$pbkdf2-sha256$29000$UAqBcA6hVGrtvbd2LkW'
             'odQ$4nNngNTkEn0d3WzDG31gHKRQ2sVvnJuLudwoynT137Y'), #Hash of 'password'
            ['demo'],
            ['personal'],
            data={
                'name':'Tester Testy'
            },
            state='live'
        )    
        user2.to_db()

        #Request just users with jordan accounts and check correct data is returned
        response = User.get_all('jordan',['email','roles'])
        expected = [{
            'username': user1.username, 
            'roles': user1.roles, 
            'email': user1.email
        }]
        
        self.assertEqual( response, expected )
        
        #Request a different attribute set of users with demo or jordan accounts.
        response = User.get_all(['jordan', 'demo'],'email')
        
        #We don't know what order the responses will be returned in.
        for item in response:
            if item['username'] == user1.username:
                self.assertEqual( item['email'], user1.email )
            elif item['username'] == user2.username:
                self.assertEqual( item['email'], user2.email )
            else:
                self.assertTrue( False )

        #Request all users and all attributes.
        response = User.get_all([], None)

        #We don't know what order the responses will be returned in.
        for item in response:
            if item['username'] == user1.username:
                self.assertEqual( item, user1.to_dict() )                
            elif item['username'] == user2.username:
                self.assertEqual( item, user2.to_dict() )     
            else:
                self.assertTrue( False )


