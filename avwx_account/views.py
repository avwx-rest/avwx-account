"""
avwx_account.views - App routing and view logic
"""

from flask import redirect, render_template
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
def home():
    return render_template('index.html')

@app.route('/manage')
@login_required
def manage():
    return render_template('manage.html')

@app.route('/token')
@login_required
def generate_token():
    current_user.new_token()
    return redirect('manage')

@app.route('/token/<token>')
def verify_token(token):
    user = User.query.filter_by(apitoken=token).first()
    if user:
        if user.active_token:
            return 'Valid token'
        return 'Token is not active'
    return 'Invalid token'
