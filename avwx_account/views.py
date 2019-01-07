"""
avwx_account.views - App routing and view logic
"""

from flask import redirect, render_template
from flask_user import login_required, current_user
from avwx_account import app
from avwx_account.models import User
from avwx_account.payment import plans

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/manage')
@login_required
def manage():
    return render_template('manage.html')

# Payment management

@app.route('/activate/<plan>', methods=['GET', 'POST'])
@login_required
def activate(plan: str):
    try:
        plan_data = plans[plan]
    except KeyError:
        redirect('home.html')
    return render_template('activate.html',
        stripe_key=app.config['STRIPE_PUB_KEY'],
        plan_tag=plan,
        plan_description=plan_data['description'],
        plan_price=plan_data['price'] * 100,
        email=current_user.email,
    )

# Token management

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
