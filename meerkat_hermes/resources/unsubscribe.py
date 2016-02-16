"""
This class manages provides a public facing gateway to unsubscribe someone from the system. 
Specifically it provides a means for folk who know their subscriber ID, to unsubscribe themselves.
A sutbale link can then be included in all emssages that are sent out. 
"""
import uuid, boto3, json
from flask_restful import Resource, reqparse
from flask import current_app, Response
from boto3.dynamodb.conditions import Key, Attr
from meerkat_hermes.resources.subscribe import Subscribe

#The Unsubscribe resource has two methods, one to throw up a confirmation dialouge and one to delete.
class Unsubscribe(Resource):

    def __init__(self):
        #Load the database and tables, upon object creation. 
        self.db = boto3.resource('dynamodb')
        self.subscribers = self.db.Table(current_app.config['SUBSCRIBERS'])
        self.subscriptions = self.db.Table(current_app.config['SUBSCRIPTIONS'])

    def get(self, subscriber_id):
        """
        Returns a page that allows the user to confirm they wish to delete their subscriptions

        Args:
             subscriber_id
        Returns:
             The amazon dynamodb response.
        """

        html = "<html><head><title>Unsubscribe Confirmation</title></head>"
        html += "<body><H2>Unsubscribe Confirmation</H2>" 
        html += "<p>Are you sure you want to unsubscribe?</p>" 
        html += "<form action='/unsubscribe/"+subscriber_id+"' method='POST'>" 
        html += "<input type='submit' value='Confirm'> </form> </body> </html>"

        return html

    def post(self, subscriber_id):
        """
        Actually performs the deletion by calling the DELETE method in subscribe. 
        We don't directly call the delete method from the above html in order to hide the api key.
        
        Args:
             subscriber_id
        Returns:
             The amazon dynamodb response.
        """
        Subscribe().delete(subscriber_id)
        
