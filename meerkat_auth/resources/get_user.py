import calendar, time, meerkat_auth, json
from flask_restful import Resource, reqparse
from flask import Response, current_app, jsonify, request
from meerkat_auth.util.user import User, InvalidCredentialException
from meerkat_auth.util.role import InvalidRoleException
from meerkat_auth.require_jwt import require_jwt

class GetUser(Resource):
    """This class returns a User object for a given JWT."""

    @require_jwt(['registered'])
    def get(self, payload):
        """
        Return a user object in JSON for a given JWT. 

        Arguments are passed in the request data.

        Args:
            jwt (str)

        Returns:
            A json object detailing the user associated with the given JWT. 
            
        """

        current_app.logger.warning(payload)
        


        
