"""
avwx_account.__init__ - High-level Flask application
"""

from os import environ
from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Load config vars from env
# These will overwrite vars in config.py and .env if found
for key in (
    'SECRET_KEY',
    'SQLALCHEMY_DATABASE_URI',
    'SECURITY_PASSWORD_SALT',
    'MAIL_USERNAME',
    'MAIL_PASSWORD',
):
    if app.config.get(key) is None:
        app.config[key] = environ.get(key)

db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

from avwx_account import admin, user_manager, views
