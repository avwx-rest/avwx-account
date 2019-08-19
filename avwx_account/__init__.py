"""
AVWX account and token management portal
"""

# stdlib
from os import environ, path

# library
import rollbar
from flask import Flask, got_request_exception
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from mailchimp3 import MailChimp
from rollbar.contrib.flask import report_exception

app = Flask(__name__)
app.config.from_pyfile("config.py")


def load_env():
    """
    Load config vars from env
    These will overwrite vars in config.py and .env if found
    """
    for key in (
        "SECRET_KEY",
        "SQLALCHEMY_DATABASE_URI",
        "SECURITY_PASSWORD_SALT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "STRIPE_PUB_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_SIGN_SECRET",
        "ROOT_URL",
        "MC_LIST_ID",
    ):
        if app.config.get(key) is None:
            app.config[key] = environ.get(key)


load_env()

db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

mc = MailChimp(mc_api=environ.get("MC_KEY"), mc_user=environ.get("MC_USERNAME"))


@app.before_first_request
def init_rollbar():
    """
    Initialize Rollbar exception logging
    """
    key = environ.get("LOG_KEY")
    if not (key and app.env == "production"):
        return
    rollbar.init(
        key,
        root=path.dirname(path.realpath(__file__)),
        allow_logging_basic_config=False,
    )
    got_request_exception.connect(report_exception, app)


from avwx_account import admin, user_manager, views
