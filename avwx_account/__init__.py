"""
AVWX account and token management portal
"""

# stdlib
from datetime import datetime
from os import environ, path

# library
import rollbar
from rollbar.contrib.flask import report_exception
from flask import Flask, got_request_exception
from flask_mail import Mail
from flask_migrate import Migrate
from flask_mongoengine import MongoEngine
from mailchimp3 import MailChimp
from pymongo import MongoClient

app = Flask(__name__)
app.config.from_pyfile("config.py")


def load_env():
    """Load config vars from env
    These will overwrite vars in config.py and .env if found
    """
    for key in (
        "MAIL_PASSWORD",
        "MAIL_USERNAME",
        "MC_KEY",
        "MC_LIST_ID",
        "MC_USERNAME",
        "MONGO_URI",
        "ROOT_URL",
        "SECRET_KEY",
        "SECURITY_PASSWORD_SALT",
        "STRIPE_PUB_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_SIGN_SECRET",
        "RECAPTCHA_PUBLIC_KEY",
        "RECAPTCHA_PRIVATE_KEY",
    ):
        value = environ.get(key)
        if value is not None:
            app.config[key] = value

    app.config["MONGODB_SETTINGS"] = {"db": "account", "host": app.config["MONGO_URI"]}


load_env()

db = MongoEngine(app)
mdb = MongoClient(app.config["MONGO_URI"])
mail = Mail(app)
migrate = Migrate(app, db)
mc = MailChimp(mc_api=app.config["MC_KEY"], mc_user=app.config["MC_USERNAME"])


@app.before_first_request
def init_rollbar():
    """Initialize Rollbar exception logging"""
    key = environ.get("LOG_KEY")
    if not (key and app.env == "production"):
        return
    rollbar.init(
        key,
        root=path.dirname(path.realpath(__file__)),
        allow_logging_basic_config=False,
    )
    got_request_exception.connect(report_exception, app)


@app.template_filter("timestamp")
def format_timestamp(value: int, dt_format: str = r"%d %b %Y %I:%M %p") -> str:
    """Formats a timestamp int into a datetime string"""
    return datetime.fromtimestamp(value).strftime(dt_format)


@app.template_filter("datetime")
def format_datetime(value: datetime, dt_format: str = r"%d %b %Y %I:%M %p") -> str:
    """Formats a datetime object into a datetime string"""
    return value.strftime(dt_format)


from avwx_account import admin, graphs, user_manager, views
