"""
config.py

Configuration and settings
"""


class Config(object):
    DEBUG = False
    TESTING = False

class Production(Config):
    DEBUG = False
    TESTING = False


class Development(Config):
    DEBUG = True
    TESTING = True


class Testing(Config):
    DEBUG = False
    TESTING = True
