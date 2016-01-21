#!/usr/bin/env python3
"""
Meerkat Hermes Tests

Unit tests for the Meerkat frontend
"""

import json, unittest, boto3, meerkat_hermes

class MeerkatHermesTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_hermes.app.config['TESTING'] = True
        self.app = meerkat_hermes.app.test_client()
        #Load the database 
        self.db = boto3.resource('dynamodb')
        self.subscribers = self.db.Table('hermes_subscribers')

    def tearDown(self):
        pass

    def test_addSubscriber(self):
        subscriber=dict(
            first_name='Test',
            last_name='Test',
            email='test@test.com',
            sms='01234567891',
            topics=['Test1','Test2']
        )
        put_response = self.app.put('/subscriber', data=subscriber, follow_redirects=True)
        print( put_response.data['subscriber_id'] )
        get_response = self.subscribers.get_item( 
            Key={
                'subscriber_id': int(put_response.data['subscriber_id'])
            }
        )
        self.assertExists( get_response['Item'] )
        self.assertEquals( subscriber.email, get_response['Item']['email'] )


        
if __name__ == '__main__':
    unittest.main()
