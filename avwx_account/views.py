"""
avwx_account.views - App routing and view logic
"""

# library
import rollbar
from flask import flash, redirect, render_template, request
from flask_login import logout_user
from flask_user import login_required, current_user
from mailchimp3.mailchimpclient import MailChimpError

# app
from avwx_account import app, db, mc, payment

# from avwx_account.models import User


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/manage")
@login_required
def manage():
    return render_template("manage.html", plan=current_user.plan)


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    email = ""
    if request.method == "POST":
        email = request.form["email"]
        if email == current_user.email:
            payment.cancel_subscription()
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash("Your account has been deleted", "success")
            return redirect("")
        else:
            flash("Email does not match", "error")
    return render_template("delete_account.html", form_email=email)


@app.route("/subscribe")
@login_required
def subscribe():
    try:
        mc.lists.members.create(
            app.config.get("MC_LIST_ID"),
            {"email_address": current_user.email, "status": "subscribed"},
        )
    except MailChimpError as exc:
        data = exc.args[0]
        if data.get("title") != "Member Exists":
            rollbar.report_message(data)
    return redirect("manage")


# Payment management


@app.route("/activate/<plan>", methods=["GET", "POST"])
@login_required
def activate(plan: str):
    if current_user.plan:
        flash("You are already subscribed to AVWX", "info")
        return redirect("manage")
    try:
        plan_data = payment.PLANS[plan]
    except KeyError:
        return redirect("home")
    if request.method == "POST":
        payment.new_subscription(plan, request.form["stripeToken"])
        flash(
            f"Your {plan} plan is now active. Thank you for supporting AVWX. You can now generate your API token",
            "success",
        )
        return redirect("manage")
    else:
        return render_template(
            "activate.html",
            stripe_key=app.config["STRIPE_PUB_KEY"],
            plan_tag=plan,
            plan_description=plan_data["description"],
            plan_price=plan_data["price"],
            stripe_price=plan_data["price"] * 100,
            email=current_user.email,
        )


@app.route("/change/<plan>", methods=["GET", "POST"])
@login_required
def change(plan: str):
    try:
        plan_data = payment.PLANS[plan]
    except KeyError:
        return redirect("home")
    if not current_user.plan:
        flash("You currently do not subscribe to a plan", "info")
        return redirect("manage")
    elif current_user.plan == plan:
        flash(f"You are already subscribed to the {plan} plan", "info")
        return redirect("manage")
    if request.method == "POST":
        payment.change_subscription(plan)
        flash(
            f"Your {plan} plan is now active. Thank you for your continued support!",
            "success",
        )
        return redirect("manage")
    return render_template(
        "change.html",
        old_plan=current_user.plan,
        new_plan=plan,
        new_plan_price=plan_data["price"],
        change_type="upgrade" if plan == "enterprise" else "downgrade",
    )


@app.route("/cancel", methods=["GET", "POST"])
@login_required
def cancel():
    if not current_user.plan:
        flash("You currently do not subscribe to a plan", "info")
        return redirect("manage")
    if request.method == "POST":
        payment.cancel_subscription()
        current_user.clear_token()
        db.session.commit()
        flash("Your plan to AVWX has been cancelled", "success")
        return redirect("manage")
    return render_template("cancel.html")


# Token management


@app.route("/token")
@login_required
def generate_token():
    if current_user.apitoken and not current_user.active_token:
        flash("Your API token has been disabled. Contact michael@mdupont.com", "error")
    elif current_user.new_token():
        db.session.commit()
        flash("Your new API token is now active", "success")
    else:
        flash(
            "Your API token could not be generated. Do you have an active subscription?",
            "error",
        )
    return redirect("manage")


# @app.route('/token/<token>')
# def verify_token(token):
#     user = User.query.filter_by(apitoken=token).first()
#     if user:
#         if user.active_token:
#             return 'Valid token'
#         return 'Token is not active'
#     return 'Invalid token'
