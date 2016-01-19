"""
This class manages the Subscriber database field.  It includes methods to update the
the dynamodb table "hermes_subscribers", which stores the subscriber's first and last name,
their e-mail and optionally their mobile phone number, and finally, which topics they wish
to receive messages about. 
"""
from flask_restful import Resource, reqparse
import uuid, boto3, json
from flask import jsonify

#Load the database 
db = boto3.resource('dynamodb')
table = db.Table('hermes_subscribers')

#Define an argument parser for creating a new subscriber.
parser = reqparse.RequestParser()
parser.add_argument('first_name', required=True, type=str, help='First name of the subscriber')
parser.add_argument('last_name', required=True, type=str, help='Last name of the subscriber')
parser.add_argument('email', required=True, type=str, help='Email address of the subscriber')
parser.add_argument('sms', required=False, type=str, help='Mobile phone number of the subscriber')
parser.add_argument('topics', action='append', required=True, 
                    type=str, help='List of topics the subscriber wishes to subscribe to')

#The Subscriber resource has just two methods - to create a new user and to deleted an existing user.
class Subscriber(Resource):

    def put(self):
        """
        Add a new subscriber. Parse the given arguments to check it is a valid subscriber.
        Assign the subscriber a uuid in hex that is used to identify the subscriber when
        wishing to delete it.

        Returns:
            The amazon dynamodb response.
        """
        args = parser.parse_args()
        subscriber = {
            'id': uuid.uuid4().hex,
            'first_name': args['first_name'],
            'last_name': args['last_name'],
            'email': args['email'],
            'sms': args['sms'],
            'topics': args['topics'] 
        }
        response = table.put_item( Item=subscriber )
        return response, 200

    def delete(self, subscriber_id):
        """
        Delete a subscriber from the database. At the moment, if a user wishes to change
        information, they need to delete themselves and then re-add themselves with the
        new information.

        Args:
             subscriber_id
        Returns:
             The amazon dynamodb response.
        """
        response = table.delete_item( 
            Key={
                'id':subscriber_id
            }
        )

        return response, 200
