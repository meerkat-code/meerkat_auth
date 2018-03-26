from meerkat_auth import app
import logging


class Role:

    """
    Class to model a single access Role object and includes functions to handle
    writing, reading, deleting details from the database.
    """

    def __init__(self, country, role, description, parents, visible=[]):
        """
        Constructor for a role object.

        Args:
            country (string) The country the role belongs to.
            role (string) The unique (within country) title of the role.
            description (string) A description of the role.
            parents ([string]) A list of roles from which this role inherits
                access. The role will also inherit access that its parents
                inherits.
            visible ([string]) A list of roles required in order to view and
                use this role. Empty list [] denotes freely available.
        """
        self.country = country
        self.role = role
        self.description = description
        self.parents = parents
        self.visible = visible

    def __repr__(self):
        """
        Override to create a better string representation of a Role object.
        """
        parents = ', '.join(self.parents)
        if self.visible != []:
            visible = "visible:[{}]".format(", ".join(self.visible))
        else:
            visible = ""

        return '<{}: {}-{} parents:[{}] {} {}>'.format(
            self.__class__.__name__,
            self.role,
            self.country,
            parents,
            visible,
            self.description
        )

    def __eq__(self, other):
        """Override to define equality of Role objects."""
        return self.country == other.country and self.role == other.role

    def __ne__(self, other):
        """Override to define inequality of Role objects."""
        return self.country != other.country or self.role != other.role

    def __hash__(self):
        """Override to define the hash of Role objects."""
        return hash((self.country, self.role))

    def validate(self):
        """
        Validates the current role data as being acceptable to write to the
        database. The role must have a valid ancestor list.

        Raises:
            InvalidRoleException if the self role is not valid.
        """
        logging.debug("Validating object:\n" + repr(self))
        # Throws an Invalid Role exception if an ancestor object doesn't exist.
        self.all_access_objs()

    def to_db(self):
        """
        Writes this user object to the database table specified by
        config['ROLES'].

        Returns:
            The amazon dynamodb response.
        """
        # Validate the object.
        self.validate()

        # Use the db adapter to write the object to the database.
        logging.debug("Object validated. Writing object to database.")
        response = app.db.write(
            app.config['ROLES'],
            {'country': self.country, 'role': self.role},
            {'description': self.description,
             'parents': self.parents,
             'visible': self.visible}
        )

        # Return the response.
        logging.debug("Response from database:\n" + str(response))
        return response

    def all_access_objs(self):
        """
        Returns an array of Role objects corresponding to each of this
        Role's "anscestors" by recursively looking at each role's parents
        list.  The list also includes this Role object (self).

        Returns:
            List of ancestor Role objects.

        Raises:
            InvalidRoleException if an ancestor is not in the DB.
        """

        def get_parents(role_obj):
            parents = [role_obj]
            for parent in role_obj.parents:
                    parent_obj = Role.from_db(self.country, parent)
                    parents += get_parents(parent_obj)
            return parents

        # Remove duplicates but maintain order.
        # The fact that higher access appears further left is used in places.
        all_access = []
        for i in get_parents(self) + [self]:
            if i not in all_access:
                all_access.append(i)

        return all_access

    def all_access(self):
        """
        Returns an array of strings where each string corresponds to the
        Role title of a "parent" role. The list also includes the title
        of this Role (self).  Note this list is different to the roles
        "parents" property, because it includes all ancestors, not just
        immediate parents.  It also includes itself.

        Returns:
            List of ancestor role title strings.
        """
        return [o.role for o in self.all_access_objs()]

    @staticmethod
    def from_db(country, role):
        """
        Static method that creates a python object for a given username using
        data fetched from the database table specified by config['USERS'].
        Args:
            username (str)
        Returns:
            The python User object for the given username.
        """
        # Load data
        logging.debug(
            'Loading role "' + role + '" for ' + country + ' from database.'
        )
        response = app.db.read(
            app.config['ROLES'],
            {'country': country, 'role': role},
        )
        # Build and return object
        logging.debug('Response from database:\n' + str(response))
        if not response:
            raise InvalidRoleException(
                country, role, "Role not found in the database."
            )
        else:
            role = Role(
                response['country'],
                response['role'],
                response['description'],
                response['parents'],
                visible=response.get('visible', [])
            )
            logging.debug('Returning role:\n' + repr(role))
            return role

    @staticmethod
    def delete(country, role):
        """
        Static method that deletes account data corresponding to the given
        username from the database table specified by config['USERS'].
        Args:
            username (str)
        Returns:
            The amazon dynamodb response.
        """
        logging.debug('Deleting role ' + role + ' in ' + country)
        response = app.db.delete(
            app.config['ROLES'],
            {'country': country, 'role': role}
        )
        logging.debug("Response from database:\n" + str(response))
        return response

    @staticmethod
    def validate_role(country, role):
        """
        Checks that the specified role already exists in the db and is valid.
        A valid role has an complete ancestor list (roles from which it
        inherits access).

        Args:
            country (str) The country that role we are validating belongs to.
            role (str) The title of the role we are validating.

        Raises:
            InvalidRoleException if the role is not valid
        """
        # Raises InvalidRoleException if role not in DB.
        obj = Role.from_db(country, role)

        # Raises an InvalidRoleException if it finds a parent not in the DB.
        obj.all_access_objs()

    @staticmethod
    def get_all(country):
        """
        Fetches from the database the requested all roles that belong to the
        specified country.
        If country equates to false then all country roles will be returned.

        Args:
            countries ([str]) A list of countries for which we want the roles.
        Returns:
            A list where each element is a python dictionary detailing a single
            role.
        """

        # Set things up.
        logging.debug(
            'Loading roles for country ' + str(country) + ' from database.'
        )

        # Allow any value for countries that equates to false.
        conditions = {}
        if country:
            conditions = {'country': country}

        # Use the db adapter to get and return all roles.
        response = app.db.get_all(app.config['ROLES'], conditions)
        logging.warning(response)
        return response


class InvalidRoleException(Exception):
    """
    An exception to be raised when an invalid role is requested. An Invalid
    role is a role not found in the database, or a role without a cvalid
    complete ancestor list (the list roles from which it inherits access).
    An invalid ancestor list includes a role that doesn't exist in
    the database.
    """
    def __init__(self, country, role, message=""):
        """Create the exception"""
        self.country = country
        self.role = role
        self.message = message

    def __str__(self):
        """Readable string to print, not including the invalid value."""
        return "The role '{}' is invalid for the country '{}'. {}".format(
            self.role, self.country, self.message
        )

    def __repr__(self):
        """More compact read out of the exceptions details."""
        return "INVALID ROLE: {}-{} not valid. {}".format(
            self.country, self.role, self.message
        )
