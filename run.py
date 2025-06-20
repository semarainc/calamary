# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import logging
from sys import exit
from decouple import config as env_config
from config import config_dict
from app import create_app, db
from flask_migrate import Migrate

# Pilih mode dari ENV, default Debug
CONFIG_MODE = env_config('FLASK_ENV', default='Debug').capitalize()
try:
    app_config = config_dict[CONFIG_MODE]
except KeyError:
    exit('Error: Invalid <CONFIG_MODE>. Expected values [Debug, Production]')

app = create_app(app_config)
migrate = Migrate(app, db)

if app_config.DEBUG:
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('DEBUG       = %s', app_config.DEBUG)
    app.logger.info('Environment = %s', CONFIG_MODE)
    app.logger.info('DBMS        = %s', app_config.SQLALCHEMY_DATABASE_URI)

if __name__ == "__main__":
    app.run(port=8000)
