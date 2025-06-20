# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from decouple import AutoConfig
config = AutoConfig()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = config('SECRET_KEY', default='SECUREKEYHEREHEHEHE123!@#')
    MAX_CONTENT_LENGTH = config('MAX_CONTENT_LENGTH', default=4 * 1024 * 1024)
    UPLOADED_IMAGES_DEST = config('UPLOADED_IMAGES_DEST', default="base/static/assets/kandidat")
    UPLOAD_EXTENSIONS = config('UPLOAD_EXTENSIONS', default=['.jpg', '.png', '.gif'])
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Default: SQLite absolut, bisa override via .env
    SQLALCHEMY_DATABASE_URI = config(
        'SQLALCHEMY_DATABASE_URI',
        default='sqlite:///' + os.path.join(basedir, 'database', 'pemira.db')
    )

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

class DebugConfig(Config):
    DEBUG = True
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
