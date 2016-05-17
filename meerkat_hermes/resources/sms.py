"""
This resource provides a simple means of sending a given e-mail message to given e-mail addresses.
"""
from flask_restful import Resource, reqparse
import uuid, boto3, uuid, json
from flask import current_app, Response
import meerkat_hermes.util as util
from meerkat_hermes.authentication import require_api_key

#This simple Emailer resource has just one method, which sends a given email message.
class Sms(Resource):

    #Require authentication
    decorators = [require_api_key]    

    def put(self):
        """
        Send an sms message with Nexmo. 
        First parse the given arguments to check it is a valid sms.

        Arguments are passed in the request data.

        Args:
            sms (str): The destination phone number.\n
            message (str): The sms message.

        Returns:
            The Nexmo response.
        """ 

        #Define an argument parser for creating a valid email message.
        parser = reqparse.RequestParser()
        parser.add_argument('sms', required=True, type=str, help='The destination phone number')
        parser.add_argument('message', required=True, type=str, help='The message to be sent')

        args = parser.parse_args()
        response = util.send_sms( 
            args['sms'], 
            args['message']
        )

        #Log the message
        message_id = 'G'+uuid.uuid4().hex
        util.log_message( message_id, {
            'destination':[args['sms']], 
            'medium':['sms'], 
            'time':util.get_date(),
            'message':args['message']
        })
        response['log_id'] = message_id
            
        return Response( json.dumps( response ), 
                         status=200,
                         mimetype='application/json' )
