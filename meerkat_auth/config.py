"""
config.py

Configuration and settings
"""
from importlib import util
from psycopg2 import sql
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
    ROOT_URL = os.environ.get("MEERKAT_AUTH_ROOT", "")

    SENTRY_DNS = os.environ.get('SENTRY_DNS', '')
    if SENTRY_DNS:
        # Generate javascript sentry_dns
        end = SENTRY_DNS.split("@")[1]
        begining = ":".join(SENTRY_DNS.split(":")[:-1])
        SENTRY_JS_DNS = begining + "@" + end

    # DB Adapters from meerkat libs enable us to use different dbs.
    DB_ADAPTER = os.environ.get("MEERKAT_DB_ADAPTER", "DynamoDBAdapter")
    DB_ADAPTER_CONFIGS = {
        "DynamoDBAdapter": {
            'db_url': os.environ.get(
                "DB_URL",
                "https://dynamodb.eu-west-1.amazonaws.com"
            ),
            "structure": {
                ROLES: {
                    "TableName": ROLES,
                    "AttributeDefinitions": [
                        {'AttributeName': 'country', 'AttributeType': 'S'},
                        {'AttributeName': 'role', 'AttributeType': 'S'}
                    ],
                    "KeySchema": [
                        {'AttributeName': 'country', 'KeyType': 'HASH'},
                        {'AttributeName': 'role', 'KeyType': 'RANGE'}
                    ],
                    "ProvisionedThroughput": {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                USERS: {
                    "TableName": USERS,
                    "AttributeDefinitions": [
                        {'AttributeName': 'username', 'AttributeType': 'S'}
                    ],
                    "KeySchema": [
                        {'AttributeName': 'username', 'KeyType': 'HASH'}
                    ],
                    "ProvisionedThroughput": {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            }
        },
        'PostgreSQLAdapter': {
            'db_name': 'meerkat_auth',
            'structure': {
                USERS: [
                    ("username", sql.SQL("username VARCHAR(50) PRIMARY KEY")),
                    ("data",  sql.SQL("data JSON"))
                ],
                ROLES: [
                    ("country", sql.SQL("country VARCHAR(50)")),
                    ("role", sql.SQL("role VARCHAR(50)")),
                    ("data", sql.SQL("data JSON"))
                ]
            }
        }
    }


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
