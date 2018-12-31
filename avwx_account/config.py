"""
avwx_account.config - App config vars
"""

# Flask Settings

# Flask-SQLAlchemy settings
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Security settings
SECURITY_PASSWORD_HASH='pbkdf2_sha512'

# Flask-Mail SMTP server settings
MAIL_SERVER = 'smtp.mailgun.org'
MAIL_PORT = 587

# Flask-User settings
USER_APP_NAME = "AVWX"
USER_ENABLE_EMAIL = True
USER_ENABLE_USERNAME = False
USER_EMAIL_SENDER_NAME = USER_APP_NAME
USER_EMAIL_SENDER_EMAIL = "noreply@avwx.rest"
USER_AFTER_CHANGE_PASSWORD_ENDPOINT = "manage"
USER_AFTER_CONFIRM_ENDPOINT = "manage"
USER_AFTER_EDIT_USER_PROFILE_ENDPOINT = "manage"
USER_AFTER_FORGOT_PASSWORD_ENDPOINT = "manage"
USER_AFTER_LOGIN_ENDPOINT = "manage"
