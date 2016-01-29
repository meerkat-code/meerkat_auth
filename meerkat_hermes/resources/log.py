"""
This class enables management of the message log.  It includes methods to get the entire log
or to get a single    
"""
import uuid, boto3, json
from flask_restful import Resource, reqparse
from flask import jsonify, current_app
from boto3.dynamodb.conditions import Key, Attr
from meerkat_hermes.authentication import require_api_key


#The Subscriber resource has just two methods - to create a new user and to deleted an existing user.
class Log(Resource):

    def __init__(self):
        #Load the database and tables, upon object creation. 
        self.db = boto3.resource('dynamodb')
        self.log = self.db.Table(current_app.config['LOG'])

    def get(self, log_id):
        """
        Get message log records from the database. 

        Args:
             log_id - The id of the desired message log. 

        Returns:
             The amazon dynamodb response.
        """

        #Require authentication
        decorators = [require_api_key]

        response = self.log.get_item( 
            Key={
                'id':log_id
            }
        )
        if 'Item' in response:
            return response, 200 
        else:
            return "400 Bad Request: log_id doesn't exist", 400

    def delete(self, log_id):
        """
        Delete a log record from the database.

        Args:
             log_id for the record to be deleted.
        Returns:
             The amazon dynamodb response.
        """

        #Require authentication
        decorators = [require_api_key]

        log_response = self.log.delete_item( 
            Key={
                'id':log_id
            }
        )    
        
        return log_response, 200
