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

    # Load the authentication settings file.
    filename = os.environ.get('MEERKAT_AUTH_SETTINGS')
    exec(compile(open(filename, "rb").read(), filename, 'exec'))

    DEBUG = False
    TESTING = False

    USERS = 'auth_users'
    ROLES = 'auth_roles'
    TOKEN_LIFE = 3600  # Max length of a sign in session in seconds.

    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = ["en", "fr"]

    DB_URL = from_env("DB_URL", "https://dynamodb.eu-west-1.amazonaws.com")
    ROOT_URL = from_env("MEERKAT_AUTH_ROOT", "")

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
