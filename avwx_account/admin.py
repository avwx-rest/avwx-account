"""
Customizes the admin portal
"""

# library
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.form import SecureForm
from flask_security.utils import encrypt_password
from flask_user import current_user
from wtforms.fields import PasswordField

# module
from avwx_account import app
from avwx_account.models import Plan, User


class AuthIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_roles("Admin")


class AuthModel(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_roles("Admin")


class UserAdmin(AuthModel):

    column_exclude_list = ("password", "tokens")
    form_excluded_columns = ("password",)
    form_base_class = SecureForm
    column_auto_select_related = True

    def scaffold_form(self) -> SecureForm:
        """
        Add a change password field to User form
        """
        form_class = super(UserAdmin, self).scaffold_form()
        form_class.password2 = PasswordField("New Password")
        return form_class

    def on_model_change(self, form: SecureForm, model: User, is_created: bool):
        """
        Encrypt the new password if given
        """
        if model.password2:
            model.password = encrypt_password(model.password2)


admin = Admin(app, index_view=AuthIndexView())

admin.add_view(UserAdmin(User))
admin.add_view(AuthModel(Plan))
