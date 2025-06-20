# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
Copyright (c) 2021 - Semara (semarainc)
"""

import os
from flask import Flask, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler

db = SQLAlchemy()
login_manager = LoginManager()

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    # Penting: import models agar user_loader/request_loader terdaftar
    from app.base import models

def register_blueprints(app):
    from app.base.routes import blueprint as base_blueprint
    from app.home.routes import blueprint as home_blueprint
    app.register_blueprint(base_blueprint)
    app.register_blueprint(home_blueprint)

def configure_database(app):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

def ensure_sqlite_folder(app):
    """Hanya untuk SQLite: pastikan folder tujuan ada."""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '', 1)
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

def create_app(config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    ensure_sqlite_folder(app)
    register_cli_commands(app)
    return app

def register_cli_commands(app):
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database (create all tables, for dev/test only)."""
        from app.base import models
        db.create_all()
        models.AddAdmin()  # Tambahkan admin default setelah create_all
        print("Database initialized (all tables created) and default admin created.")
