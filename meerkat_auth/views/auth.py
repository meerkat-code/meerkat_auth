"""
auth.py

A Flask Blueprint module for the authentication api calls.
"""
from flask import Blueprint, Response, current_app, jsonify
from flask import make_response, request, redirect
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import InvalidRoleException
from meerkat_auth import app

import calendar
import time
import json
import jwt

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/', methods=['POST'])
@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    Try to log a new user in. If a correct username and password have been
    provided we return a jwt to the user that can be used to login into any
    part of meerkat. Parameters are passed in the POST request data.

    Args:
        username (str): The users username
        password (str): The users password

    Returns:
        A json object containing a single argument 'message', stating \
            'successful' or the error message.

    Raises:
        InvalidRoleException: Indicating the user doesn't have a valid role.
        InvalidCredentialException: Indicating the user has specified an
            invalid username or password.
    """

    # Load the form's data.
    args = request.json

    # Try to authenticate the user and set JWT in a cookie
    # Expiry time is taken from account data, or defaults to config value.
    try:
        user = User.authenticate(args['username'], args['password'])
        current_app.logger.warning("Authenticated: " + str(user))
        expiry = calendar.timegm(time.gmtime()) + int(user.data.get(
            'TOKEN_LIFE',
            {'val': app.config['TOKEN_LIFE']}
        )['val'])
        response = jsonify({'message': 'successful'})
        response.set_cookie(
            app.config['JWT_COOKIE_NAME'],
            value=user.get_jwt(expiry)
        )
        return response

    # If we get a failed credential exception return a 401 http error.
    except InvalidCredentialException as e:
        current_app.logger.info(repr(e))
        response = jsonify({'message': str(e)})
        response.status_code = 401
        return response

    # If we get a failed role exception return a 500 http error.
    except InvalidRoleException as e:
        current_app.logger.info(repr(e))
        response = jsonify(
            {'message': 'Your account has broken access levels.'}
        )
        response.status_code = 500
        return response


@auth_blueprint.route('/get_user', methods=['POST'])
def get_user():
    """
    Return all user data that doesn't need to be in the header. Headers need
    to be kept small, and our "access" dictionary was starting to get too big.
    The access details, personal data and account settings are bundled up in a
    big signed JWT that is servered upon request. Parameters are passed in the
    POST request data.

    Args:
        jwt (str): The signed JWT for which we should get the user details.

    Returns:
        A json object detailing the user associated with the given JWT.
    """
    try:
        token = request.json['jwt']
        token = jwt.decode(
            token,
            app.config['JWT_PUBLIC_KEY'],
            algorithms=[app.config['JWT_ALGORITHM']]
        )

        user = User.from_db(token['usr'])
        exp = calendar.timegm(time.gmtime()) + 60
        return_json = {'jwt': user.get_user_jwt(exp)}

        # Return the large jwt with a short expiry time.
        # It only needs to be decoded once at the other end.
        return jsonify(return_json)

    # If we fail to get the user from the database to return a 500 http error.
    except Exception as e:
        current_app.logger.warning(repr(e))
        return Response(
            json.dumps({'message': str(e)}),
            status=500,
            mimetype='application/json'
        )


@auth_blueprint.route('/logout')
def logout():
    """
    Logs a user out. This involves delete the current jwt stored in a cookie
    and redirecting to the specified page.  We delete a cookie by changing it's
    expiration date to immediately. Set the page to be redirected to using url
    params, eg. /logout?url=https://www.google.com. Parameters are passed as
    GET args in the request.

    Args:
        url (str): The url of the page to redirect to after logging out.

    Returns:
        A redirect response object that also sets the cookie's expiration time
        to 0.
    """
    url = request.args.get('url', '/')
    response = make_response(redirect(url))
    response.set_cookie(app.config["JWT_COOKIE_NAME"], value="", expires=0)
    return response


@auth_blueprint.route('/update_user', methods=['POST'])
def update_user():
    """
    An API call that updates the specified users details.  Can be used to reset
    passwords. THIS IS AUTHENTICATED using the the username and password
    given in the post args, which is why no other authorisation is needed.
    Parameters are passed as POST args in the request.

    Args:
        username (str): The username of the user to be updated.
        old_password (str): The original user's passowrd (it may be changed). \
            Any of the attributes of a user's object can also be suplied.

    Returns:
        A json object containing a single argument 'message', stating \
        'successful' or the error message.
    """
    # Load the form's data.
    args = request.json

    try:
        # Check user has supplied their old username and password correctly.
        user = User.authenticate(
            args.pop('username'),
            args.pop('old_password')
        )
    except Exception as e:
        current_app.logger.info('Failed to authenticate. ' + repr(e))
        return Response(
            json.dumps({'message': 'Failed to authenticate. ' + str(e)}),
            status=500,
            mimetype='application/json'
        )

    try:
        # Update each argument supplied correctly.
        failed = []
        for arg in args.keys():
            # Need to hash the password.
            if arg == 'password':
                args[arg] = User.hash_password(args[arg])
            try:
                setattr(user, arg, args[arg])
            except AttributeError:
                failed.append(arg)
        # Write the user to the database (this validates the user as well).
        user.to_db()
        # Return response
        if not failed:
            return jsonify({'message': 'successful'})
        else:
            return jsonify(
                {'message': 'Failed to update attributes: {}'.format(failed)}
            )

    # Handle any authentication/validation exceptions
    except Exception as e:
        current_app.logger.info('Failed to write. ' + repr(e))
        return Response(
            json.dumps({'message': 'Failed to write. ' + str(e)}),
            status=500,
            mimetype='application/json'
        )
