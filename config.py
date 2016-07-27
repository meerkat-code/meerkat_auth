"""
config.py

Configuration and settings
"""


class Config(object):
    DEBUG = False
    TESTING = False

    USERS = 'auth_users'
    ROLES = 'auth_roles'
    TOKEN_LIFE = 3600 #Max length of a sign in session in seconds.

    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = ["en", "fr"]

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
