#!/usr/bin/env python3
"""
Meerkat Hermes Tests

Unit tests for the Meerkat frontend
"""

import json, unittest, boto3, meerkat_hermes
import meerkat_hermes.util as util
from boto3.dynamodb.conditions import Key, Attr

class MeerkatHermesTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_hermes.app.config['TESTING'] = True
        self.app = meerkat_hermes.app.test_client()
        #Load the database 
        db = boto3.resource('dynamodb')
        self.subscribers = db.Table('hermes_subscribers')
        self.log = db.Table('hermes_log')

    def tearDown(self):
        """At the end of testing, clean up any database mess created by the tests."""
        #First get rid of any undelted test subscribers.
        query_response = self.subscribers.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq('test@test.com')
        )
        with self.subscribers.batch_writer() as batch:
            for subscriber in query_response['Items']:
                batch.delete_item(
                    Key={
                        'id': subscriber['id']
                    }
                ) 
        #Get rid of any test messages that have been logged. 
        query_response = self.log.query(
            IndexName='message-index',
            KeyConditionExpression=Key('message').eq('Nosetest Message')
        )
        
        with self.log.batch_writer() as batch:
            for message in query_response['Items']:
                batch.delete_item(
                    Key={
                        'id': message['id']
                    }
                ) 

    def test_subscriber(self):
        """Test the Subscriber resource, including the PUT, GET and DELETE methods."""
        #Define the test subscriber
        subscriber=dict(
            first_name='Test',
            last_name='Test',
            email='test@test.com',
            sms='01234567891',
            topics=['Test1','Test2']
        )
        #Create the test subscriber
        put_response = self.app.put('/subscribe', data=subscriber )
        #Get the assigned subscriber id.
        data = json.loads( put_response.data.decode('UTF-8') )
        subscriber_id =data['subscriber_id']
        print( "Subscriber ID is " + data['subscriber_id'] )
        #Check that the subscriber exists in the data base.
        get_response = self.subscribers.get_item( 
            Key={
                'id': data['subscriber_id']
            }
        )
        self.assertEquals( subscriber['email'], get_response['Item']['email'] )
        #Try to delete the subscriber.
        delete_response = self.app.delete( '/subscribe/'+subscriber_id )
        #Get the response and check it equals 200.
        data = json.loads( delete_response.data.decode('UTF-8') )
        self.assertEquals( data['ResponseMetadata']['HTTPStatusCode'], 200 )

    def test_email(self):
        """Test the Email resource using the Amazon SES Mailbox Simulators."""
        #Define the email
        email=dict(
            subject='Test email',
            message='Nosetest Message',
            html='Test <b>HTML</b> message',
            email='success@simulator.amazonses.com'
        )
        #Send the email and check that it returns a 200 OK status code
        email_response = self.app.put('/email', data=email)
        data = json.loads( email_response.data.decode('UTF-8') ) 
        self.assertEquals( data['ResponseMetadata']['HTTPStatusCode'], 200 )
        #Check that the message has been logged properly.
        get_response = self.log.get_item( 
            Key={
                'id': data['log_id']
            }
        )
        self.assertEquals( get_response['Item']['destination'][0], email['email'] )

    def test_replace_keywords(self):
        """Test the replace keywords utility function that enables mail merge in our messages."""
        subscriber = {
            "email": "test@test.com",
            "first_name": "Janet",
            "id": "772b814e5d3a4321aed03c1fa694484f",
            "last_name": "Berry",
            "sms": "+441234567890",
            "topics": [
                "Topic1", "Topic2", "Topic3"
            ]
        }
        for key in subscriber:
            message = "<<"+key+">>"
            value = str(subscriber[key])
            if( key == 'topics' ):
                value = "Topic1, Topic2 and Topic3"
            self.assertEquals( value, util.replace_keywords(message, subscriber) )
        
if __name__ == '__main__':
    unittest.main()
