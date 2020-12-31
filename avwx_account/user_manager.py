"""
Customize flask-user management system
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,attribute-defined-outside-init

from flask_login import AnonymousUserMixin
from flask_user import UserManager
from flask_user.forms import RegisterForm
from flask_wtf import RecaptchaField

from avwx_account import app, db
from avwx_account.models import User


class CustomRegisterForm(RegisterForm):
    recaptcha = RecaptchaField()


class CustomUserManager(UserManager):
    def customize(self, _):
        self.RegisterFormClass = CustomRegisterForm


user_manager = CustomUserManager(app, db, User)


class Anonymous(AnonymousUserMixin):
    """Say that anonymous users have no roles"""

    @staticmethod
    def has_roles(*_) -> bool:
        return False


user_manager.anonymous_user = Anonymous
