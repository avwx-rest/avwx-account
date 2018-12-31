"""
avwx_account.views - App routing and view logic
"""

from flask import redirect, render_template
from flask_user import login_required, current_user
from avwx_account import app
from avwx_account.models import User

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
