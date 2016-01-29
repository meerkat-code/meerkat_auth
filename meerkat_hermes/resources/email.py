"""
This resource provides a simple means of sending a given e-mail message to given e-mail addresses.
"""
from flask_restful import Resource, reqparse
import uuid, boto3, json, uuid
from flask import jsonify, current_app
import meerkat_hermes.util as util
from meerkat_hermes.authentication import require_api_key


#This simple Emailer resource has just one method, which sends a given email message.
class Email(Resource):

    def put(self):
        """
        Send an email with Amazon SES. 
        First parse the given arguments to check it is a valid email.
        !!!Remember that whilst still in AWS "Sandbox" we can only send to verified emails.

        PUT args:
            'subject'* - The e-mail subject (String)
            'message'* - The e-mail message (String)
            'email'* - The destination address/es for the e-mail (String)
            'html' - The html version of the message, will default to the same as 'message' (String)

        Returns:
            The amazon SES response.
        """

        #Require authentication
        decorators = [require_api_key]

        #Define an argument parser for creating a valid email message.
        parser = reqparse.RequestParser()
        parser.add_argument('subject', required=True, type=str, help='The email subject')
        parser.add_argument('message', required=True, type=str, help='The message to be sent')
        parser.add_argument('email', required=True, action='append', type=str, 
                            help='The destination address')
        parser.add_argument('html', required=False, type=str, 
                            help='If applicable, the message in html')

        args = parser.parse_args()
        response = util.send_email( 
            args['email'], 
            args['subject'], 
            args['message'], 
            args['html'] 
        )

        message_id = 'G'+uuid.uuid4().hex

        util.log_message( message_id, {
            'destination': args['email'], 
            'medium': ['email'], 
            'time': util.get_date(),
            'message': args['message']
        })

        response['log_id'] = message_id
            
        return response, 200
