"""
This resource provides a simple means of sending a given e-mail message to given e-mail addresses.
"""
from flask_restful import Resource, reqparse
import uuid, boto3, json
from flask import jsonify, current_app
import meerkat_hermes.util as util

#Load the database 
db = boto3.resource('dynamodb')
table = db.Table('hermes_subscribers')

#Define an argument parser for creating a valid email message.
parser = reqparse.RequestParser()
parser.add_argument('subject', required=True, type=str, help='The email subject')
parser.add_argument('message', required=True, type=str, help='The message to be sent')
parser.add_argument('email', required=True, action='append', type=str, 
                    help='The destination address')
parser.add_argument('html', required=False, type=str, 
                    help='If applicable, the message in html')

#This simple Emailer resource has just one method, which sends a given email message.
class Emailer(Resource):

    def put(self):
        """
        Send an email with Amazon SES. 
        First parse the given arguments to check it is a valid email.

        PUT args:
            'subject' - The e-mail subject.
            'message' - The e-mail message.
            'email' - The destination address/es for the e-mail.
            'html' - The html version of the message, will default to the same as 'message'

        Returns:
            The amazon SES response.
        """
        args = parser.parse_args()

        response = util.send_email( 
            args['email'], 
            args['subject'], 
            args['message'], 
            args['html'] 
        )
    
        return response, 200
