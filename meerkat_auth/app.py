"""
app.py

Creating the root Flask app from the meerkat authentication module.
"""

from flask import Flask
from flask.ext.babel import Babel

# Create the Flask app
app = Flask(__name__)
babel = Babel(app)
app.config.from_object('config.Production')
app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
