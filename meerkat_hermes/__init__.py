"""
meerkat_hermers.py

Root Flask app for the Meerkat Hermes messaging module.
"""
from flask import Flask
from flask.json import JSONEncoder
from flask_restful import Api, reqparse
import boto3

from meerkat_hermes.resources.test import Subscriber

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Development')
app.config.from_envvar('MEERKAT_HERMES_SETTINGS', silent=True)
api=Api(app)

#Load the database 
db = boto3.resource('dynamodb')
table = db.Table('hermes_subscribers')

#display something at /
@app.route('/')
def hello_world():
    return table.creation_date_time.strftime('%d/%m/%Y')

#The api
api.add_resource(Subscriber, "/subscriber", "/subscriber/<string:subscriber_id>")
