"""
"""

from flask import render_template
from flask_user import UserManager, login_required, roles_required
from avwx_account import app, db
from avwx_account.models import User

user_manager = UserManager(app, db, User)

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/members')
@login_required
def member_page():
    return render_template('members.html')

@app.route('/admin')
@roles_required('Admin')
def admin_page():
    return render_template('admin_page.html')
