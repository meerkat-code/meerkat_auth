"""
users.py

A Flask Blueprint module for the user manager page.
"""
from flask import Blueprint, render_template, request, jsonify, g, abort
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import InvalidRoleException
from meerkat_auth.authorise import auth
from meerkat_auth import app, add_domain
import datetime
import logging

users_blueprint = Blueprint('users', __name__, url_prefix="/<language>")


@users_blueprint.before_request
def requires_auth():
    """
    Checks that the user has authenticated before returning any page from
    this Blueprint.
    """
    auth.check_auth(['admin'], [''])

    # Only allow admin's to edit accounts in their own countries.
    # i.e. if admin has non-admin access to another country.
    countries = list(g.payload['acc'].keys())
    for country in countries:
        if 'admin' not in g.payload['acc'][country]:
            del g.payload['acc'][country]

    logging.warning(g.payload['acc'])


def compare_access(roles, countries):
    """
    Utility function to check that the current user has access to the
    specified access levels.  Aborts the request if current user doesn't have
    access.

    Args:
        roles ([str]): A list of access role names, to compare the current
            users access against.
        countries ([str]): The corresponding countries for each role in roles.
    """
    user_access = g.payload['acc']
    # Look at each access level the account has.
    for i in range(len(roles)):
        acc_role = roles[i]
        acc_country = countries[i]
        # If the account has an access level the current user doesn't have:
        # (If the current user has access in that country...)
        if acc_role not in user_access.get(acc_country, [acc_role]):
            abort(403, "You are not authorised to view or edit this user.")


@users_blueprint.route('/get_users')
def get_users():
    """
    Get a list of users for the bootstrap table listing users.  We do not allow
    people to see accounts that have access they themselves do not have.

    Returns:
        A json response containing one property "rows" which is a list of
        objects where each object represents a row of the user accounts table.
    """
    # Set attributes "to get"
    # And restrict accounts shown, to those from the user's countries.
    acc = g.payload['acc']
    countries = list(acc.keys())
    attributes = [
        "email", "roles", "username", "countries", "creation", "data"
    ]
    rows = User.get_all(countries, attributes)

    # Remove any data rows (accounts) that are outside the users access.
    # Step backwards through the list so we can smoothly delete as we go.
    for j in range(len(rows)-1, -1, -1):
        access = (rows[j]['roles'], rows[j]['countries'], acc)
        if not auth.check_access(*access, 'AND'):
            del rows[j]

    return jsonify({'rows': rows})


@users_blueprint.route('/get_user/')
@users_blueprint.route('/get_user/<username>')
def get_user(username=""):
    """
    Get the specified user as a json reponse.

    Args:
        username (str) The username of the user to get.

    Returns:
        A json response containing all the details of the specified user
        as specified by the User object "to_dict()" method.  If no username
        is given, this method returns an empty user. This is useful for
        js design in the frontend (means we always have value to auto-fill
        the user editor form with).
    """
    if username == "":
        return jsonify({
          "countries": [],
          "creation": "",
          "data": {},
          "email": "",
          "password": "",
          "roles": [],
          "state": "",
          "updated": "",
          "username": ""
        })

    else:
        user = User.from_db(username)
        # Check that the current user has access to view the requested user.
        auth.check_auth(user.roles, user.countries, 'AND')
        return jsonify(user.to_dict())


@users_blueprint.route('/check_username/<username>')
def check_username(username):
    """
    Checks whether or not the specified username is a valid new username.

    Args:
        username (str) the username to check

    Returns:
        A json response with a single property 'valid', set to true if valid
        and false if not.
    """

    return jsonify({'valid': not User.check_username(username)})


@users_blueprint.route('/update_user/<username>', methods=['POST'])
@users_blueprint.route('/update_user/', methods=['POST'])
def update_user(username='new'):
    """
    Update/create a user. If username is set to "new" it will create and
    validate as a new user.  Pass the new user details as json int he post
    data. Post data should contain the following properties: username, email,
    password, countries (list of str), roles (list of str), state, creation
    (timestamp), data (json object). Look at the db to see the structure of
    data.

    Args:
        username (str) The username of the user to be updated.

    Returns:
        A string stating success or error.
    """
    # Load the form's data and check the current user has access to edit.
    data = request.get_json()
    auth.check_access(data["roles"], data["countries"], 'AND')
    if username != 'new':
        user = User.from_db(username)
        auth.check_auth(user.roles, user.countries, 'AND')

    # Form's password field default is empty, only update if something entered.
    # Original password hash is stored in hidden input so we don't need to
    # reload user here.
    if data["password"]:
        data["password"] = User.hash_password(data["password"])
    else:
        data["password"] = data["original_password"]

    # Create a user object represented by the form input.
    user = User(
        data["username"],
        data["email"],
        data["password"],
        data["countries"],
        data["roles"],
        state=data["state"],
        updated=datetime.datetime.now().isoformat(),
        creation=data["creation"],
        data=data["data"]
    )
    logging.warning(
        "Original username: " + username + " New username: " + data['username']
    )

    # If username changed, then create a new record for validation.
    # ...because otherwise validation will say "username already exists".
    if username != data["username"]:
        user.state = "new"

    # Factor out the multiple lines of error handling for writing to database.
    def write(user):
        try:
            user.to_db()
        except (InvalidRoleException, InvalidCredentialException) as e:
            return str(e)
        except Exception as e:
            return str(e)
            raise

    # Write the user to the database. Includes server-side validation.
    write(user)

    # Reset state once validation and writing complete
    # Changing username shouldn't wipe the state.
    if user.state != data["state"]:
        user = User.from_db(user.username)
        user.state = data["state"]
        write(user)

    # When username changes we create a new db record, so delete old one.
    if username != data["username"]:
        User.delete(username)

    return "Successfully Updated"


@users_blueprint.route('/delete_users', methods=['POST'])
def delete_users():
    """
    Delete the users specified in the post arguments.
    The post arguments takes a list of usernames to be deleted.

    Returns:
        A string either stating success or the existance of an error.
    """

    # Load the list of users to be deleted.
    users = request.get_json()

    # Try to delete users
    try:
        for username in users:
            # Check current user has access to delete the specified user.
            user = User.from_db(username)
            auth.check_auth(user.roles, user.countries, logic='AND')
            # Delete the user
            User.delete(username)
    except Exception as e:
        return ("Unfortunately there was an error:\n " + str(e) +
                "\nContact the administrator if the problem persists.")

    return "Users succesfully deleted."


@users_blueprint.route('/')
def index():
    """Renders the user editor/creator/viewer page."""
    return render_template(
        'users/index.html',
        user=g.payload,
        root=add_domain(app.config['ROOT_URL'])
    )
