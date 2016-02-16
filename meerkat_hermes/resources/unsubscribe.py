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
import meerkat_hermes.util as util

#The Unsubscribe resource has two methods, one to throw up a confirmation dialouge and one to delete.
class Unsubscribe(Resource):

    def get(self, subscriber_id):
        """
        Returns a page that allows the user to confirm they wish to delete their subscriptions

        Args:
             subscriber_id
        Returns:
             The amazon dynamodb response.
        """
        current_app.logger.warning( "Unsubscriber called")

        html = ( "<html><head><title>Unsubscribe Confirmation</title></head>"
                 "<body><H2>Unsubscribe Confirmation</H2>" 
                 "<p>Are you sure you want to unsubscribe?</p>" 
                 "<form action='/unsubscribe/" + subscriber_id + "' method='POST'>" 
                 "<input type='submit' value='Confirm'> </form> </body> </html>" )

        return Response( html,
                         status=200,
                         mimetype='text/html' )

    def post(self, subscriber_id):
        """
        Actually performs the deletion. 
        
        Args:
             subscriber_id
        Returns:
             The amazon dynamodb response.
        """

        return util.delete_subscriber( subscriber_id )
        
