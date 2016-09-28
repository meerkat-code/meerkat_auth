from datetime import datetime
from meerkat_auth.role import Role
from passlib.hash import pbkdf2_sha256
from flask import jsonify
import meerkat_auth, uuid, logging, boto3, jwt, re, json

class User:
    """
    Class to model a single User's account and manage writing, reading, deleting
    from the database.
    """

    #The regular expression defining whether an email address is valid.
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
    #The database resource
    DB = boto3.resource(
        'dynamodb', 
        endpoint_url=meerkat_auth.app.config['DB_URL'], 
        region_name='eu-west-1'
    )
    
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
        access = ','.join(
            '({}|{})'.format(*t) for t in zip(self.countries, self.roles)
        )  
        updated = "" if self.creation == self.updated else "|" + self.updated

        return '<{}: {}({}) email: {} pass: {} access: [{}] time: ({}{})>'.format(
            self.__class__.__name__, 
            self.username,
            self.state,
            self.email,
            self.password,
            access,
            self.creation,
            updated
        )  
         
    def __str__(self):
        """Override to create a better string representation of a User object."""
        access = ','.join(
            '({}|{})'.format(*t) for t in zip(self.countries, self.roles)
        )  
        updated = "" if self.creation == self.updated else "|" + self.updated

        return '<{}: {}({}) email: {} access: [{}]>'.format(
            self.__class__.__name__, 
            self.username,
            self.state,
            self.email,
            access,
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
        users = User.DB.Table(meerkat_auth.app.config['USERS'])

        #If new user, set the state as live now it is going into the db and add the creation timestamp.
        if self.state == "new":
            self.creation = datetime.now().isoformat()
            self.state = "live" 

        logging.warning("Data type: " + str(type(self.data) ) )

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
        secret = meerkat_auth.app.config['JWT_SECRET_KEY']
        algorithm = meerkat_auth.app.config['JWT_ALGORITHM']
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
        users = User.DB.Table(meerkat_auth.app.config['USERS'])
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
                state=r.get('state', 'undefined'),
                updated=r.get('updated', 'undefined'),
                creation=r.get('creation', 'undefined'),
                data = r.get('data', {})
            )

            #We want NO NEW USERS in the database.  Do 2nd clean up here.
            user.state = "live" if user.state == "new" else user.state

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
        users = User.DB.Table(meerkat_auth.app.config['USERS'])
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
        users = User.DB.Table(meerkat_auth.app.config['USERS'])
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
    def update_user( username, email, unhashed_pass, countries, roles, data={} ):
        """
        Utility function to help update user objects. 
        Validates and prepares the data given, loads the user from db, edits the users 
        data and writes the user to the db before returning the final user to the caller. 
        Preparation includes the hashing of the new password.

        Args:
            username (str) Must be unique in the database.
            email (str) Must be a valid email address.
            unhashed_pass (str) The unhashed password.
            countries ([str]) A list of countries the account has access to.
            roles ([str]) A corresponding list of access roles for each country
                with the same index in the countries argument.

        Returns:
            The user object if it has been successfully validated.
    
        Raises:
            InvalidCredentialException if the username or password isn't valid.
            InvalidRoleException if a role doesn't exist or doesn't have a valid
                ancestor list.
        """
        
        #Hash the password with a random salt size of 16 bytes and 29000 rounds.
        hashed_pass = User.hash_password( unhashed_pass )
        

        #Create the user, write it to db and return the object.
        user = User.from_db( username )
        user.username = username
        user.email = email
        user.password = hashed_pass
        user.countries = countries 
        user.roles = roles
        user.updated = datetime.now().isoformat()
        if( data ):
            user.data = data

        #Validate the details
        user.validate()
        
        #Update and return
        user.to_db()
        return user

    @staticmethod
    def get_all(countries, attributes):
        """
        Fetches from the database the requested attributes for all users that belong
        to the specified country. If country or attributes equate to false then
        all possible options for that argument will be used.
    
        Args:
            country ([str]) A list of countries for which we want user accounts.  This is an OR
                list - i.e. any account attached to ANY of the countries in the list is retruned.
            attributes ([str]) A list of user account attribute names that we want to download.

        Returns:
            A python dictionary storing user accounts by username.
        """
        #Set things up.
        logging.info('Loading users for country ' + str(countries) + ' from database.')
        table = User.DB.Table(meerkat_auth.app.config['USERS']) 
 
        #Allow any value for attributes and countries that equates to false.
        if not attributes:
            attributes = []
        if not countries:
            countries = []

        #If a single value is specified, but not as a list, turn it into a list.
        if not isinstance(countries, list):
            countries = [countries]
        if not isinstance(attributes, list):
            attributes = [attributes]
  
        #Add username to attributes if not already included, as return dict is indexed by them.
        if attributes and 'username' not in attributes:
            attributes.append('username')

        #Assemble scan arguments programatically, by building a dictionary.
        kwargs = {}

        #Include AttributesToGet if any are specified (by not including them we get them all).
        if attributes:
            kwargs["AttributesToGet"] = attributes

        if not countries:
            #If no country is specified, get all users and return as list.
            return table.scan(**kwargs).get("Items", [])

        else:
            users = {}
            #Load data separately for each country because Scan can't perform OR on CONTAINS
            for country in countries:

                kwargs["ScanFilter"]={
                    'countries': {
                        'AttributeValueList':[country], 
                        'ComparisonOperator':'CONTAINS'
                    }
                } 

                #Get and combine the users together in a no-duplications dict indexed by username.
                for user in table.scan(**kwargs).get("Items", []):
                    users[user["username"]] = user 
                
            #Convert the dict to a list by getting values.
            return list(users.values())

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
        return "Invalid credential supplied. Please check the {} and try again.".format(
            self.credential
        )

    def __repr__(self):
        """String referencing both the invalid credential and the its invalid value."""
        return "INVALID CREDENTIALS: {} '{}' is not valid. {}".format(
            self.credential, self.value, self.message
        )
