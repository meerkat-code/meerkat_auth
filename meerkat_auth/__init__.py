"""
meerkat_hermers.py

Root Flask app for the Meerkat Hermes messaging module.
"""
from flask import Flask, redirect, g 
from flask.json import JSONEncoder
from flask_restful import Api, reqparse
from flask.ext.babel import Babel, gettext, ngettext, get_translations, get_locale, support
import boto3
from meerkat_auth.views.users import users
from meerkat_auth.views.roles import roles


# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Production')
app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
api=Api(app)
babel = Babel(app)

# Import the API resources
# Import them after creating the app, because they depend upon the app.
from meerkat_auth.resources.login import Login
from meerkat_auth.resources.get_user import GetUser

# Add the API  resources.
api.add_resource(Login, "/login")
api.add_resource(GetUser, "/user")

# Internationalisation for the backend
@babel.localeselector
def get_locale():
    return g.get("language", app.config["DEFAULT_LANGUAGE"])

@users.url_value_preprocessor
@roles.url_value_preprocessor
def pull_lang_code(endpoint, values):
    language = values.pop('language')
    if language not in app.config["SUPPORTED_LANGUAGES"]:
        abort(404, "Language not supported")
    g.language = language

@users.url_defaults
@roles.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('language', app.config["DEFAULT_LANGUAGE"])

# Register the Blueprint modules for the backend
app.register_blueprint(users, url_prefix='/<language>/users')
app.register_blueprint(roles, url_prefix='/<language>/roles')

@app.route("/")
def root():
    return redirect("/" + app.config["DEFAULT_LANGUAGE"])

#display something at /
@app.route('/')
def hello_world():
    """Display something at /.  
       This method loads a dynamodb table and displays its creation date.
    """
    return "Meerkat_Auth"
