"""
This class enables management of the message log.  It includes methods to get the entire log
or to get a single    
"""
import uuid, boto3, json
from flask_restful import Resource, reqparse
from flask import Response current_app
from boto3.dynamodb.conditions import Key, Attr
from meerkat_hermes.authentication import require_api_key

#The Subscriber resource has just two methods - to create a new user and to deleted an existing user.
class Log(Resource):

    #Require authentication
    decorators = [require_api_key]

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

        response = self.log.get_item( 
            Key={
                'id':log_id
            }
        )
        if 'Item' in response:
            return Response( data=jsonify(response), status=200, mimetype="application/json" ) 
        else:
            message =  {"message":"400 Bad Request: log_id doesn't exist"}
            return Response( data=jsonify(message), status=400, mimetype="application/json" ) 

    def delete(self, log_id):
        """
        Delete a log record from the database.

        Args:
             log_id for the record to be deleted.
        Returns:
             The amazon dynamodb response.
        """

        log_response = self.log.delete_item( 
            Key={
                'id':log_id
            }
        )    
        
        return Response( data=jsonify( log_response ), 
                         status=response['responseMetaData']['HTTPStatusCode'],
                         mimetype='application/json' )
