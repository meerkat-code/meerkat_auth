"""
auth.py

A Flask Blueprint module for the authentication api calls.
"""
import calendar, time, meerkat_auth, json
from flask_restful import Resource, reqparse
from flask import Blueprint, Response, current_app, jsonify, make_response, request, redirect
from meerkat_auth.user import User, InvalidCredentialException
from meerkat_auth.role import InvalidRoleException
from meerkat_auth.require_jwt import require_jwt

auth = Blueprint('auth', __name__, url_prefix="/<language>")

@auth.route('/', methods=['POST'])
@auth.route('/login', methods=['POST'])
def login():
    """
    Try to log a new user in. If a correct username and password have been provided
    we return a jwt to the user that can be used to login into any part of 
    meerkat. 

    Arguments are passed in the request data.

    Post data json args:
        username (str)\n
        password (str)\n
        redirect (

    Returns:
        A json object containing a single argument 'message', stating 'successful'
        or the error message.

    Raises:
        InvalidRoleException
        InvalidCredentialException
    """

    #Load the form's data.
    args = request.json

    #Try to authenticate the user and set JWT in a cookie
    try:
        user = User.authenticate( args['username'], args['password'] )
        exp = calendar.timegm( time.gmtime() ) + meerkat_auth.app.config['TOKEN_LIFE']
        response = make_response( jsonify( {'message':'successful'} ) ) 
        response.set_cookie( 
            meerkat_auth.app.config['COOKIE_NAME'], 
            value=user.get_jwt(exp)
        )
        return response
    
    #If we get a failed credential exception return a 401 http error.
    except InvalidCredentialException as e:
        current_app.logger.info( repr(e) )
        response = jsonify( {'message': str(e)} )
        response.status_code = 401
        return response

    #If we get a failed role exception return a 500 http error.
    except InvalidRoleException as e:
        current_app.logger.info( repr(e) )
        response = jsonify( {'message': 'Your account has broken access levels.'} )
        response.status_code = 500
        return response

@auth.route('/get_user', methods=['POST'])
def get_user():
    """
    Return a user object in JSON for a given JWT. 

    Arguments are passed in the request data.

    Args:
        jwt (str)

    Returns:
        A json object detailing the user associated with the given JWT. 
    """
    
    try: 
        return User.from_db(payload['usr']).to_json()

    #If we fail to get the user from the database return a 500 http error.
    except Exception as e:
        current_app.logger.info( repr(e) )
        return Response( 
            json.dumps( {'message':str(e)} ), 
            status=500, 
            mimetype='application/json'  
        )


@auth.route('/logout')
def logout():
    """
    Logs a user out. This involves delete the current jwt stored in a cookie and 
    redirecting to the specified page.  We delete a cookie by changing it's
    expiration date to immediately. Set the page to be redirected to using url
    params, eg. /logout?url=https://www.google.com

    Get Args:
        url (str) The url of the page to redirect to after logging out.

    Returns:
        A redirect response object that also sets the cookie's expiration time to 0.
    """
    url = request.args.get('url', '/')
    response = make_response( redirect(url) )
    response.set_cookie( meerkat_auth.app.config["COOKIE_NAME"], value="", expires=0 )
    return response
    
