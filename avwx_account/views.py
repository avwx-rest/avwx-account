"""
avwx_account.views - App routing and view logic
"""

from flask import render_template
from flask_login import AnonymousUserMixin
from flask_user import UserManager, login_required, roles_required, current_user
from avwx_account import app, db
from avwx_account.models import User

user_manager = UserManager(app, db, User)

# Say that anonymous users have no roles
class Anonymous(AnonymousUserMixin):
    def has_roles(self, *_) -> bool:
        return False
user_manager.anonymous_user = Anonymous

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/members')
@login_required
def member_page():
    return render_template('members.html')
