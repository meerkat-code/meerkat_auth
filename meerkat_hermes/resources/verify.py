"""
If the subscriber hasn't been verified, their subscriptions to different topics will not have been 
created. This resource is used after a subscriber's details have been verified, to make their subscriptions
active.
"""
import uuid, boto3, json
from flask_restful import Resource, reqparse
import meerkat_hermes.util as util
from flask import current_app, Response
from boto3.dynamodb.conditions import Key, Attr
from meerkat_hermes.authentication import require_api_key

class Verify(Resource):

    #Require authentication
    decorators = [require_api_key]

    def __init__(self):
        #Load the database and tables, upon object creation. 
        self.db = boto3.resource('dynamodb')
        self.subscribers = self.db.Table(current_app.config['SUBSCRIBERS'])
        self.subscriptions = self.db.Table(current_app.config['SUBSCRIPTIONS'])

    def get(self, subscriber_id):
        """
        Creates the subscriptions and sets the subscriber's "verified" attribute to True. 

        Args:
             subscriber_id - The ID for the subscriber who has been verified. 
        Returns:
             The amazon dynamodb response.
        """

        #Check subscriberID doesn't exist in subscriptions already
        exists = self.subscriptions.query(
            IndexName='subscriberID-index',
            KeyConditionExpression=Key('subscriberID').eq(subscriber_id)
        )

        #Get subscriber details.
        subscriber = self.subscribers.get_item( 
            Key={
                'id':subscriber_id
            }
        )

        if not (exists or subscriber['Item']['Verfied']): 

            topics = subscriber['Item']['topics']

            #Create the subscriptions
            util.create_subscriptions( subscriber_id, topics )

            #Update the verified field.
            self.subscribers.update_item(
                Key={
                    'id': subscriber_id
                },
                UpdateExpression='SET verified = :val1',
                ExpressionAttributeValues={
                    ':val1': True
                }
            )
        
            message = { "message": "Subscriber verified" }
            return Response( json.dumps( message ), 
                             status=200,
                             mimetype='application/json' )

        else:
            message = { "message":"400 Bad Request: Subscriber has already been verified." }
            return Response( json.dumps( message ), 
                             status=400,
                             mimetype='application/json' )

