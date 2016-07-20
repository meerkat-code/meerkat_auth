import calendar, time, meerkat_auth, json
from flask_restful import Resource, reqparse
from flask import Response, current_app, jsonify
from meerkat_auth.util.user import User, InvalidCredentialException
from meerkat_auth.util.role import InvalidRoleException

class Login(Resource):
    """This class manages the Login process."""

    def post(self):
        """
        Try to log a new user in. If a correct username and password have been provided
        we return a jwt to the user that can be used to login into any part of 
        meerkat. 

        Arguments are passed in the request data.

        Args:
            username (str)\n
            password (str)\n

        Returns:
            A JWT web token.

        Raises:
            
        """

        #Define an argument parser for creating a new subscriber.
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True, type=str)
        parser.add_argument('password', required=True, type=str)
        args = parser.parse_args()

        #Try to authenticate the user and get the JWT
        try:
            user = User.authenticate( args['username'], args['password'] )
            exp = calendar.timegm( time.gmtime() ) + meerkat_auth.app.config['TOKEN_LIFE']
            return jsonify( {'jwt':user.get_jwt(exp)} )
        
        #If we get a failed credential exception return a 401 http error.
        except InvalidCredentialException as e:
            current_app.logger.info( repr(e) )
            return Response( 
                json.dumps( {'message':str(e)} ), 
                status=401, 
                mimetype='application/json'  
            )

        #If we get a failed role exception return a 500 http error.
        except InvalidRoleException as e:
            current_app.logger.info( repr(e) )
            return Response( 
                json.dumps( {'message':'Your account has broken access levels.' } ), 
                status=500, 
                mimetype='application/json'  
            )
        
