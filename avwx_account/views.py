"""
avwx_account.views - App routing and view logic
"""

from flask import flash, redirect, render_template, request
from flask_user import login_required, current_user
from avwx_account import app, payment
from avwx_account.models import User

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/manage')
@login_required
def manage():
    return render_template('manage.html',
        plan=current_user.plan,
    )

# Payment management

@app.route('/activate/<plan>', methods=['GET', 'POST'])
@login_required
def activate(plan: str):
    if current_user.plan:
        flash('You are already subscribed to AVWX')
        return redirect('manage')
    try:
        plan_data = payment.PLANS[plan]
    except KeyError:
        return redirect('home')
    if request.method == 'POST':
        payment.new_subscription(plan, request.form['stripeToken'])
        return redirect('success')
    else:
        return render_template('activate.html',
            stripe_key=app.config['STRIPE_PUB_KEY'],
            plan_tag=plan,
            plan_description=plan_data['description'],
            plan_price=plan_data['price'],
            stripe_price=plan_data['price'] * 100,
            email=current_user.email,
        )

@app.route('/success')
@login_required
def success():
    return render_template('success.html')

@app.route('/change/<plan>', methods=['GET', 'POST'])
@login_required
def change(plan: str):
    try:
        plan_data = payment.PLANS[plan]
    except KeyError:
        return redirect('home')
    if current_user.plan == plan:
        flash(f'You are already subscribed to the {plan} plan')
        return redirect('manage')
    if request.method == 'POST':
        payment.change_subscription(plan)
        return redirect('success')
    return render_template('change.html',
        old_plan=current_user.plan,
        new_plan=plan,
        new_plan_price=payment.PLANS[plan]['price'],
        change_type='upgrade' if plan == 'enterprise' else 'downgrade',
    )

@app.route('/cancel', methods=['GET', 'POST'])
@login_required
def cancel():
    if not current_user.plan:
        flash('You currently do not subscribe to a plan')
        return redirect('manage')
    if request.method == 'POST':
        payment.cancel_subscription()
        current_user.clear_token()
        return redirect('success')
    return render_template('cancel.html')

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
