"""
config.py

Configuration and settings
"""

import os

def from_env(env_var, default):
    """ Gets value from envrionment variable or uses default

    Args: 
        env_var: name of envrionment variable
        default: the default value
    """
    new = os.environ.get(env_var)
    if new:
        return new
    else:
        return default

class Config(object):
    DEBUG = False
    TESTING = False

    USERS = 'auth_users'
    ROLES = 'auth_roles'
    TOKEN_LIFE = 3600 #Max length of a sign in session in seconds.
    COOKIE_NAME = 'jwt'

    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = ["en", "fr"]

    DB_URL = from_env("DB_URL", "https://dynamodb.eu-west-1.amazonaws.com")
    

class Production(Config):
    DEBUG = True
    TESTING = False

class Development(Config):
    DEBUG = True
    TESTING = True

class Testing(Config):
    DEBUG = False
    TESTING = True
    USERS = 'test_auth_users'
    ROLES = 'test_auth_roles'
