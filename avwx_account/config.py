"""
avwx_account.config - App config vars
"""

from os import environ

# Flask Settings
SECRET_KEY = environ.get('SECRET_KEY')

# Flask-SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URI', 'sqlite:///test_app.sqlite')

# Flask-Mail SMTP server settings
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USE_TLS = False
MAIL_USERNAME = 'michael@avwx.rest'
MAIL_PASSWORD = 'super secret password'
MAIL_DEFAULT_SENDER = '"AVWX" <noreply@avwx.rest>'

# Flask-User settings
USER_APP_NAME = "AVWX" # Shown in and email templates and page footers
USER_ENABLE_EMAIL = True # Enable email authentication
USER_ENABLE_USERNAME = False # Disable username authentication
USER_EMAIL_SENDER_NAME = USER_APP_NAME
USER_EMAIL_SENDER_EMAIL = "noreply@avwx.rest"