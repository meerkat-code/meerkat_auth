from flask import Flask
from flask.ext.babel import Babel

# Create the Flask app
app = Flask(__name__)
babel = Babel(app)
app.config.from_object('meerkat_auth.config.Production')
app.config.from_envvar('MEERKAT_AUTH_SETTINGS')
