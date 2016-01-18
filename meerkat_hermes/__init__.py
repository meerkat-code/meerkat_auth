"""
meerkat_hermers.py

Root Flask app for the Meerkat Hermes messaging module.
"""
from flask import Flask
from flask.json import JSONEncoder
from flask_restful import Api

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Development')
app.config.from_envvar('MEERKAT_HERMES_SETTINGS', silent=True)


@app.route('/')
def hello_world():
    return "Meerkat Hermes messaging module."
