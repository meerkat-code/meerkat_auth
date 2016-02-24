"""
This class manages the Subscriber database field.  It includes methods to update the
the dynamodb tables "hermes_subscribers" and "hermes_subscriptions".  Conceptually, there are 
subscribers, there are topics (in "hermes_topics" table), and there are subscriptions which map
between subscribers and topics using their id fields.   
"""
import uuid, boto3, json
from flask_restful import Resource, reqparse
from flask import current_app, Response
from meerkat_hermes.authentication import require_api_key
import meerkat_hermes.util as util

#The Subscriber resource has just two methods - to create a new user and to deleted an existing user.

class Subscribe(Resource):

    #Require authentication
    decorators = [require_api_key]

    def __init__(self):
        #Load the database and tables, upon object creation. 
        self.db = boto3.resource('dynamodb')
        self.subscribers = self.db.Table(current_app.config['SUBSCRIBERS'])
        self.subscriptions = self.db.Table(current_app.config['SUBSCRIPTIONS'])

    def get(self, subscriber_id):
        """
        Get a subscriber's info from the database. 

        Args:
             subscriber_id - The ID for the desired subscriber. 
        Returns:
             The amazon dynamodb response.
        """
        current_app.logger.warning('Get subcriber called.  subscriber_id: ' + subscriber_id )
        response = self.subscribers.get_item( 
            Key={
                'id':subscriber_id
            }
        )
        current_app.logger.warning( 'Response from dynamodb: ' + str(response) )
        return Response( json.dumps( response ), 
                         status=response['ResponseMetadata']['HTTPStatusCode'],
                         mimetype='application/json' )

    def put(self):
        """
        Add a new subscriber. Parse the given arguments to check it is a valid subscriber.
        Assign the subscriber a uuid in hex that is used to identify the subscriber when
        wishing to delete it.

        PUT Args:
            'first_name'* - The subscriber's first name (String)
            'last_name'* - The subscriber's last name (String)
            'email'* - The subscriber's email address (String)
			'country'* - The country that the subscriber has signed up to (String)
            'sms' - The subscribers phone number for sms (String)
            'topics' - The ID's for the topics to which the subscriber wishes to subscribe ([String])
            'verified' - Are their contact details verified? Defaults to False. (Bool)

        Returns:
            The amazon dynamodb response, with the assigned subscriber_id added.
        """

        #Define an argument parser for creating a new subscriber.
        parser = reqparse.RequestParser()
        parser.add_argument('first_name', required=True, type=str, help='First name of the subscriber')
        parser.add_argument('last_name', required=True, type=str, help='Last name of the subscriber')
        parser.add_argument('email', required=True, type=str, help='Email address of the subscriber')
        parser.add_argument('country', required=True, type=str, help='Country subscribed to')
        parser.add_argument('sms', required=False, type=str, help='Mobile phone number of the subscriber')
        parser.add_argument('verified', required=False, type=bool, help='Are the contact details verified?')
        parser.add_argument('topics', action='append', required=True, 
                            type=str, help='List of topic IDs the subscriber wishes to subscribe to')

        current_app.logger.warning( "Subcribe PUT called" )

        args = parser.parse_args()
        subscriber_id = uuid.uuid4().hex
        subscriber = {
            'id': subscriber_id,
            'first_name': args['first_name'],
            'last_name': args['last_name'],
            'country': args['country'],
            'email': args['email'],
            'topics': args['topics']
        }
        if args['sms'] is not None: subscriber['sms'] = args['sms']
        if args['verified'] is not None: subscriber['verified'] = args['verfied']
        else: subscriber['verified'] = False

		current_app.logger.warning( "Adding subscriber:\n" + str(subscriber) )

        response = self.subscribers.put_item( Item=subscriber )
        response['subscriber_id'] = subscriber_id
 
        if subscriber['verified']:
            util.create_subscriptions( subscriber_id, args['topics'] )

        return Response( json.dumps( response ), 
                         status=response['ResponseMetadata']['HTTPStatusCode'],
                         mimetype='application/json' )

    @require_api_key
    def delete(self, subscriber_id):
        """
        Delete a subscriber from the database.

        Args:
             subscriber_id
        Returns:
             The amazon dynamodb response.
        """

        return util.delete_subscriber( subscriber_id )
