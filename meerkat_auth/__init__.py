"""
meerkat_hermers.py

Root Flask app for the Meerkat Hermes messaging module.
"""
from flask import Flask
from flask.json import JSONEncoder
from flask_restful import Api, reqparse
import boto3

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Production')
app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
api=Api(app)

# Import the API resources
# Import them after creating the app, because they depend upon the app.
from meerkat_auth.resources.login import Login
from meerkat_auth.resources.get_user import GetUser


# Add the API  resources.
api.add_resource(Login, "/login")
api.add_resource(GetUser, "/user")

#display something at /
@app.route('/')
def hello_world():
    """Display something at /.  
       This method loads a dynamodb table and displays its creation date.
    """
    return "Meerkat_Auth"
