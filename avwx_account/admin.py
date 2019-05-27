"""
avwx_account.admin - Generates the admin portal
"""

# library
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_user import current_user
from wtforms.fields import PasswordField

# module
from avwx_account import app, db
from avwx_account.models import Role, User


class AuthIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_roles("Admin")


class AuthModel(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_roles("Admin")


class UserAdmin(AuthModel):

    # User update issue:
    # https://github.com/flask-admin/flask-admin/issues/782#issuecomment-421886244

    column_exclude_list = ("password", "apitoken")
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
        if len(model.password2):
            model.password = utils.encrypt_password(model.password2)


admin = Admin(app, index_view=AuthIndexView())

admin.add_view(UserAdmin(User, db.session))
admin.add_view(AuthModel(Role, db.session))
