from datetime import datetime
from role import Role
from passlib.hash import pbkdf2_sha256
from flask import jsonify
import meerkat_auth, uuid, logging, boto3, jwt, re 



class User:
    """
    Class to model a single User's account and manage writing, reading, deleting
    from the database.
    """

    #The regular expression defining whether an email address is valid.
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
    
    def __init__( self,
                  username, 
                  email,
                  password,
                  countries,
                  roles,
                  state="live",
                  updated=datetime.now().isoformat(),
                  creation=datetime.now().isoformat(),
                  data = {} ):
        """Create a User object."""

        #Initalise variables
        self.username = username
        self.email = email
        self.password = password
        self.countries = countries
        self.roles = roles
        self.state=state
        self.creation = creation
        self.updated = updated
        self.data = data 

        #Create an array of role objects from the array of roles.
        self.role_objs = []
        for r in enumerate(roles):
            self.role_objs.append( Role.from_db( self.countries[r[0]], r[1] ) )       

    def __repr__(self):
        """Override to create a better string representation of a User object."""
        countries = ','.join(
            '({}|{})'.format(*t) for t in zip(self.countries, self.roles)
        )  
        updated = "" if self.creation == self.updated else "|" + self.updated

        return '<{}-{}({}) email:{} pass:{} countries:[{}] time:({}{})>'.format(
            self.__class__.__name__, 
            self.username,
            self.state,
            self.email,
            self.password,
            countries,
            self.creation,
            updated
        )                
    
    def __eq__(self, other):
        """Override to define equality of User objects."""
        return self.username == other.username
        
    def __ne__(self, other):
        """Override to define inequality of User objects."""
        return self.username != other.username

    def __hash__(self):
        """Override to define the hash of User objects."""
        return hash(username)

    def to_dict(self):
        """Returns the current object state as a python dict."""
        return {    
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'countries': self.countries,
            'roles': self.roles,
            'state': self.state,
            'creation': self.creation,
            'updated': self.updated,
            'data': self.data
        }

    def to_json(self):
        """Returns the current object state as a json string."""
        return jsonify( self.to_dict() )

    def to_db(self):
        """
        Writes this user object to the database table specified by config['USERS'].
        First validates content.

        Returns:
            The amazon dynamodb response.
        """
        #Validate
        self.validate()

        #Write to DB.
        logging.info( "Validated. Writing object to database." )
        users = boto3.resource('dynamodb').Table(meerkat_auth.app.config['USERS'])
        response = users.update_item(
            Key={
                'username':self.username
            }, 
            AttributeUpdates={
                'email':{ 'Value':self.email, 'Action':'PUT' },
                'password':{ 'Value':self.password, 'Action':'PUT' },
                'countries':{ 'Value':self.countries, 'Action':'PUT' },
                'roles':{ 'Value':self.roles, 'Action':'PUT' },
                'state':{ 'Value':self.state, 'Action':'PUT' },
                'creation':{ 'Value':self.creation, 'Action':'PUT' },
                'updated':{ 'Value':self.updated, 'Action':'PUT' },
                'data':{ 'Value':self.data, 'Action':'PUT' }
            }
        )
        logging.info( "Response from database:\n" + str(response) )

        #If this is a new user who has never been written to the db before
        if self.state == "new":
            self.state = "live"
        
        
        return response

    def get_access(self):
        """
        Returns an object detailing the complete list of roles this user has access to
        in each country. 
        
        Returns:
            A dictionary where each key is a country and each value is a list of roles 
            this user has access to in that country.
        """
        access = {}
        for role in self.role_objs:
            access[role.country] = role.all_access()
        return access

    def get_jwt(self, exp):
        """
        Returns a secure Json Web Token (JWT) giving the users details and 
        including the specified expiry time of the user's session.

        Args:
            exp (string) The expiry time of the users session.
        Returns:
            The secure jwt.
        """
        payload = {
            'exp': exp,
            'acc': self.get_access(),
            'usr': self.username,
            'email': self.email,
            'data': self.data
        }
        secret = meerkat_auth.app.config['SECRET']
        algorithm = meerkat_auth.app.config['ALGORITHM']
        return jwt.encode(payload, secret, algorithm=algorithm)

    def validate(self):
        """
        Checks whether the object is a valid user object that can be written
        to the database.

        Raises:
            InvalidCredentialException if a credential is invalid.\n
            InvalidRoleException if an ancestor role is not valid.
        """
        logging.info( "Validating User object:\n" + repr(self))

        #Raises an InvalidCredentialException if username not valid.
        if self.state == 'new':
            User.validate_username( self.username )
        else:
            if not User.check_username( self.username ):
                raise InvalidCredentialException( 
                    'username', 
                    self.username, 
                    'Username must match a username in the database.'
                )
        #Check that the password is a hash.
        if not pbkdf2_sha256.identify( self.password ):
            raise InvalidCredentialException( 
                'password', 
                self.password,
                'Password must be hashed according to the specified hashing policy.'
            )
        #Raises an InvalidRoleException if role, or ancestor role doesn't exist.
        User.validate_roles( self.countries, self.roles )
        #Raises an InvalidCredentialException if the email is not valid.
        if not User.EMAIL_REGEX.match(self.email):
            raise InvalidCredentialException( 'email', self.email )


    @staticmethod
    def authenticate( username, password ):
        """
        Checks whether the specified credentials are valid credentials for a user.
        If they are, returns the User object, if not throws an exception.

        Args:
            username (str)
            password (str)
    
        Returns:
            The authenticated user.  

        Raises:
            InvalidCredentialException if either of the credentials are invalid.
        """
  
        #Raises an exception if the username is invalid.
        user = User.from_db( username )
        #Raises an exception if the password is invalid.
        if pbkdf2_sha256.verify( password, user.password ):
            return user
        else:
            raise InvalidCredentialException('password', password)
                

    @staticmethod
    def from_db( username ):
        """
        Creates a python object for a given username using
        data fetched from the database table specified by config['USERS'].
        Args:
            username (str)
        Returns:
            The python User object for the given username.
        """
        #Load data
        logging.info('Loading user ' + username + ' from database.')
        users = boto3.resource('dynamodb').Table(meerkat_auth.app.config['USERS'])
        response = users.get_item( 
            Key={
                'username': username
            }
        )
        logging.info('Response from database:\n' + str(response))

        #Build and return object
        if not response.get("Item", None):
            raise InvalidCredentialException( 'username', username )
        else:
            r = response["Item"]
            logging.info( "RESPONSE------------\n" + repr(r) )
            user = User(
                r['username'],
                r['email'],
                r['password'],
                r['countries'],
                r['roles'],
                state=r['state'],
                updated=r['updated'],
                creation=r['creation'],
                data = r['data']
            )
            logging.info( 'Returning user:\n' + repr(user) )
            return user
    
    @staticmethod               
    def delete( username ):
        """
        Deletes account data corresponding to the given 
        username from the database table specified by config['USERS'].
        Args:
            username (str)
        Returns:
            The amazon dynamodb response.
        """
        logging.info( 'Deleting user ' + username )
        users = boto3.resource('dynamodb').Table(meerkat_auth.app.config['USERS'])
        response = users.delete_item(
            Key={
                'username':username
            }  
        ) 
        logging.info( "Response from database:\n" + str(response) )
        return response  

    @staticmethod
    def check_username( username ):
        """
        Efficiently checks whether a specific username already exists in the database.

        Args:
            username (str) 

        Returns:
            bool True if in db, False if not in db.
        """
        users = boto3.resource('dynamodb').Table(meerkat_auth.app.config['USERS'])
        response = users.get_item( 
            Key={ 'username': username },
            AttributesToGet=['username'],
        )
        if response.get("Item", None):
            return True
        else:
            return False

    @staticmethod
    def validate_username( username ):
        """
        Checks whether the specified new username is valid or not, and raises an
        InvalidCredentialException if it is not valid.

        Args:   
            username (str) The username to check the validity of.
        
        Raises:
            InvalidCredentialException if the username already exists.
        """

        if User.check_username( username ):
            raise InvalidCredentialException( 
                'username', 
                username, 
                "A 'new' username must not match a username in the database."
            )

    @staticmethod
    def validate_roles( countries, roles ):
        """
        Checks whether the supplied roles and countries lists are valid parameters
        for creating a new user.  Crucially the roles must exist in the database and
        have a valid ancestor list.
        
        Args:
            countries ([str]) A list of strings where each stirng is the name of a country.
            roles ([str]) A list of strings where eachs tring is the title of a valid role.

        Raises:
            InvalidRoleException if there is a role that does not meet the criteria.
        """
        for country, role in zip( countries, roles ):
            Role.validate_role( country, role )
 
    @staticmethod
    def validate_user( username, email, unhashed_pass, countries, roles ):
        """
        Validates the specified user details (can't duplicate usernames, roles must exist
        might want to implement a password policy, etc...)

        Args:
            username (str) Must be unique in the database.
            unhashed_pass (str) The unhashed password, to comply with any password policy.
            email (str) Must be a valid email address.
            countries ([str]) A list of countries the account has access to.
            roles ([str]) A corresponding list of access roles for each country
                with the same index in the countries argument.
    
        Raises:
            InvalidCredentialException if the username or password isn't valid.
            InvalidRoleException if a role doesn't exist or doesn't have a valid
                ancestor list.
        """               
        #Raises an InvalidCredentialException if username not valid.
        User.validate_username( username )
        #Raises an InvalidRoleException if role, or ancestor role doesn't exist.
        User.validate_roles( countries, roles )
        #Raises an InvalidCredentialException if the email is not valid.
        if not User.EMAIL_REGEX.match(email):
            raise InvalidCredentialException('email', email)
        #Can implement password policy here if desired.

    @staticmethod
    def hash_password( password ):
        """
        Hashes a string according to Meerkat's password hashing policy.
        
        Args:
            password (str) The unhashed password
        
        Returns:
            str The hashed password
        """
        return pbkdf2_sha256.encrypt(password)
    
    @staticmethod
    def new_user( username, email, unhashed_pass, countries, roles ):
        """
        Utility function to help create new user objects. 
        Validates and prepares the data given, creates a new user writes the user to the
        db and returns the user to the caller. Preparation includes the hashing of the
        password.

        Args:
            username (str) Must be unique in the database.
            email (str) Must be a valid email address.
            unhashed_pass (str) The unhashed password.
            countries ([str]) A list of countries the account has access to.
            roles ([str]) A corresponding list of access roles for each country
                with the same index in the countries argument.

        Returns:
            The new user object if it has been successfully validated.
    
        Raises:
            InvalidCredentialException if the username or password isn't valid.
            InvalidRoleException if a role doesn't exist or doesn't have a valid
                ancestor list.
        """

        #Validate the details
        User.validate_user( username, email, unhashed_pass, countries, roles )
        
        #Hash the password with a random salt size of 16 bytes and 29000 rounds.
        hashed_pass = User.hash_password( unhashed_pass )

        #Create the user, write it to db and return the object.
        user = User( username, email, hashed_pass, countries, roles, state="new" )
        user.to_db()
        return user
        

class InvalidCredentialException( Exception ):
    """
    An exception to be raised when an invalid credential is supplied, typically username
    or password. This Exception prints out the credential in the error message, but only
    prints out the invalid value supplied if you called the repr() function on the object.
    """
    def __init__(self, credential, value, message=""):
        """Create the exception"""
        self.credential = credential
        self.value = value
        self.message = message

    def __str__(self):
        """Readable string to print, not including the invalid value."""
        return "Invalid credential supplied. Please check and try again."

    def __repr__(self):
        """String referencing both the invalid credential and the its invalid value."""
        return "INVALID CREDENTIALS: {} '{}' is not valid. {}".format(
            self.credential, self.value, self.message
        )
