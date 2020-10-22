"""
App config vars
"""

# Mongo Engine settings
MONGO_URI = "mongodb://localhost:27017/account"

# Flask-Security settings
SECRET_KEY = "change my secret key"
SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
SECURITY_PASSWORD_SALT = "change my password salt"

# Flask-Mail SMTP server settings
MAIL_SERVER = "smtp.mailgun.org"
MAIL_PORT = 587
MAIL_USERNAME = "mail username"
MAIL_PASSWORD = "mail password"

# Flask-User settings
USER_APP_NAME = "AVWX"
USER_ENABLE_EMAIL = True
USER_ENABLE_USERNAME = False
USER_EMAIL_SENDER_NAME = USER_APP_NAME
USER_EMAIL_SENDER_EMAIL = "noreply@avwx.rest"
USER_AFTER_CHANGE_PASSWORD_ENDPOINT = "manage"
USER_AFTER_CONFIRM_ENDPOINT = "subscribe"
USER_AFTER_EDIT_USER_PROFILE_ENDPOINT = "manage"
USER_AFTER_FORGOT_PASSWORD_ENDPOINT = "manage"
USER_AFTER_LOGIN_ENDPOINT = "manage"

# Mailchimp Mailing List
MC_KEY = "mc api key"
MC_LIST_ID = "mc mailing list"
MC_USERNAME = "mc username"

# Mongo Token Client
MONGO_URI = None

# Stripe Payments
ROOT_URL = "http://use.ngrok.for.this.locally/"
STRIPE_PUB_KEY = "stripe public key"
STRIPE_SECRET_KEY = "stripe secret key"
STRIPE_SIGN_SECRET = "stripe webhook signing key"

# reCAPTCHA
RECAPTCHA_USE_SSL = True
RECAPTCHA_PUBLIC_KEY = "recaptcha public key"
RECAPTCHA_PRIVATE_KEY = "recaptcha private key"
RECAPTCHA_OPTIONS = {"theme": "black"}
