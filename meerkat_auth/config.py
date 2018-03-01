"""
config.py

Configuration and settings
"""
from importlib import util
import os
import logging


class Config(object):

    # Load the secret settings config file.
    # File must define JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables.
    filename = os.environ.get('MEERKAT_AUTH_SETTINGS')
    try:
        spec = util.spec_from_file_location('config', filename)
        config = util.module_from_spec(spec)
        spec.loader.exec_module(config)
    except AttributeError:
        logging.warning('Meerkat auth settings do not exist. '
                        'Will not be able to work with auth tokens')

    DEBUG = False
    TESTING = False

    USERS = 'auth_users'
    ROLES = 'auth_roles'
    TOKEN_LIFE = 3600  # Max length of a sign in session in seconds.

    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = ["en", "fr"]

    DB_URL = os.environ.get(
        "DB_URL",
        "https://dynamodb.eu-west-1.amazonaws.com"
    )
    DB_ADAPTER = os.environ.get("MEERKAT_DB_ADAPTER", "DynamoDBAdapter")
    ROOT_URL = os.environ.get("MEERKAT_AUTH_ROOT", "")

    SENTRY_DNS = os.environ.get('SENTRY_DNS', '')
    if SENTRY_DNS:
        # Generate javascript sentry_dns
        end = SENTRY_DNS.split("@")[1]
        begining = ":".join(SENTRY_DNS.split(":")[:-1])
        SENTRY_JS_DNS = begining + "@" + end


class Production(Config):
    DEBUG = False
    TESTING = False


class Development(Config):
    DEBUG = True
    TESTING = False


class Testing(Config):
    DEBUG = False
    TESTING = True
    USERS = 'test_auth_users'
    ROLES = 'test_auth_roles'
    DB_URL = "https://dynamodb.eu-west-1.amazonaws.com"
