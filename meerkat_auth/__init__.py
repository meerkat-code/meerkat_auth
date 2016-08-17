"""
meerkat_hermers.py

Root Flask app for the Meerkat Hermes messaging module.
"""
from flask import Flask, redirect, g, render_template 
from flask.json import JSONEncoder
from flask.ext.babel import Babel, gettext, ngettext, get_translations, get_locale, support
import boto3

#Import the Blueprints
from meerkat_auth.views.users import users
from meerkat_auth.views.roles import roles
from meerkat_auth.views.auth import auth

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Production')
app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
babel = Babel(app)

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
app.register_blueprint(auth, url_prefix='/auth')

#display something at /
@app.route("/")
def root():
    """Display something at /."""
    return redirect("/" + app.config["DEFAULT_LANGUAGE"] + "/")

@app.route('/<language>/')
def index(language):
    """Display something at /<language>/."""
    g.language = language
    app.logger.warning(g.language)
    return render_template('login.html')

#Handle errors
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(410)
@app.errorhandler(418)
@app.errorhandler(500)
@app.errorhandler(501)
@app.errorhandler(502)
def error500(error):
    """Serves page for generic error.
    
       Args:
           error (int): The error code given by the error handler.
    """
    return render_template('error.html', error=error,  )
