"""
avwx_account.__init__ - High-level Flask application
"""

# stdlib
from os import environ, path
# library
import rollbar
from flask import Flask, got_request_exception
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from rollbar.contrib.flask import report_exception

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
    'STRIPE_PUB_KEY',
    'STRIPE_SECRET_KEY',
    'STRIPE_BASIC_ID',
    'STRIPE_ENTERPRISE_ID',
):
    if app.config.get(key) is None:
        app.config[key] = environ.get(key)

db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

@app.before_first_request
def init_rollbar():
    """
    Initialize Rollbar exception logging
    """
    key = environ.get('LOG_KEY')
    if not (key and app.env == 'production'):
        return
    rollbar.init(
        key,
        root=path.dirname(path.realpath(__file__)),
        allow_logging_basic_config=False
    )
    got_request_exception.connect(report_exception, app)

from avwx_account import admin, user_manager, views
