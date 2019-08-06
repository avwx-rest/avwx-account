"""
App routing and view logic
"""

# library
import rollbar
from flask import flash, redirect, render_template, request, url_for
from flask_login import logout_user
from flask_user import login_required, current_user
from mailchimp3.mailchimpclient import MailChimpError
from stripe.error import CardError

# app
from avwx_account import app, db, mc, plans


@app.route("/")
def home():
    return render_template("index.html", plan=getattr(current_user, "plan", None))


@app.route("/manage")
@login_required
def manage():
    if not current_user.plan:
        current_user.plan = plans.get_plan("free")
        db.session.commit()
    return render_template("manage.html", plan=current_user.plan)


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    email = ""
    if request.method == "POST":
        email = request.form["email"]
        if email == current_user.email:
            plans.cancel_subscription()
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash("Your account has been deleted", "success")
            return redirect(url_for("home"))
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
    return redirect(url_for("manage"))


@app.route("/change/<plan>", methods=["GET", "POST"])
@login_required
def change(plan: str):
    new_plan = plans.get_plan(plan)
    if new_plan is None:
        return redirect(url_for("manage"))
    if current_user.plan == plan:
        flash(f"You are already subscribed to the {plan.name} plan", "info")
        return redirect(url_for("manage"))
    old_plan = current_user.plan
    if request.method == "POST":
        msg = f"Your {new_plan.name} plan is now active"
        # Upgrade to a paid plan
        if new_plan.price:
            if old_plan.price:
                if not plans.change_subscription(new_plan):
                    flash("Unable to update your subscription", "error")
                    return redirect(url_for("manage"))
            else:
                try:
                    plans.new_subscription(new_plan, request.form["stripeToken"])
                except CardError as exc:
                    flash(f"There was an issue with your card: {exc.get('message')}")
                    return redirect(url_for("manage"))
            msg += ". Thank you for supporting AVWX!"
        else:
            plans.cancel_subscription()
        flash(msg, "success")
        return redirect(url_for("manage"))
    return render_template(
        "change.html",
        stripe_key=app.config["STRIPE_PUB_KEY"],
        old_plan=old_plan,
        new_plan=new_plan,
    )


@app.route("/token")
@login_required
def generate_token():
    if current_user.apitoken and not current_user.active_token:
        flash("Your API token has been disabled. Contact michael@mdupont.com", "error")
    elif current_user.new_token():
        db.session.commit()
        flash(
            "Your new API token is now active. It may take up to <b>15 minutes</b> for refreshed keys to be valid in the API",
            "success",
        )
    else:
        flash(
            "Your API token could not be generated. Do you have an active subscription?",
            "error",
        )
    return redirect(url_for("manage"))
