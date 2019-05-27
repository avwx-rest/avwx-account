"""
avwx_account.views - Customize flask-user management system
"""

from flask_login import AnonymousUserMixin
from flask_user import UserManager

# from flask_user.forms import EditUserProfileForm, RegisterForm, StringField
from avwx_account import app, db
from avwx_account.models import User

# Add company field to registration and profile edit forms
# class CustomRegisterForm(RegisterForm):
#     country = StringField('Company')

# class CustomEditUserProfileForm(EditUserProfileForm):
#     country = StringField('Company')

# class CustomUserManager(UserManager):
#     def customize(self, app):
#         self.RegisterFormClass = CustomRegisterForm
#         self.EditUserProfileFormClass = CustomEditUserProfileForm

user_manager = UserManager(app, db, User)

# Say that anonymous users have no roles
class Anonymous(AnonymousUserMixin):
    def has_roles(self, *_) -> bool:
        return False


user_manager.anonymous_user = Anonymous
