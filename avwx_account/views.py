"""
App routing and view logic
"""

# library
import rollbar
from flask import flash, redirect, render_template, request, url_for
from flask_login import logout_user
from flask_user import login_required, current_user
from mailchimp3.mailchimpclient import MailChimpError
from stripe.error import SignatureVerificationError

# app
from avwx_account import app, db, mc, plans


@app.route("/")
def home():
    return render_template("index.html", plan=getattr(current_user, "plan", None))


@app.route("/manage")
@login_required
def manage():
    if not current_user.plan:
        current_user.plan = plans.Plan.by_key("free")
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
    new_plan = plans.Plan.by_key(plan)
    if new_plan is None:
        return redirect(url_for("manage"))
    if current_user.plan == new_plan:
        flash(f"You are already subscribed to the {new_plan.name} plan", "info")
        return redirect(url_for("manage"))
    old_plan = current_user.plan
    session = None
    if request.method == "POST":
        msg = f"Your {new_plan.name} plan is now active"
        if new_plan.price:
            if not plans.change_subscription(new_plan):
                flash("Unable to update your subscription", "error")
                return redirect(url_for("manage"))
            msg += ". Thank you for supporting AVWX!"
        else:
            plans.cancel_subscription()
        flash(msg, "success")
        return redirect(url_for("manage"))
    elif new_plan.price and not current_user.subscription_id:
        session = plans.get_session(new_plan)
    return render_template(
        "change.html",
        stripe_key=app.config["STRIPE_PUB_KEY"],
        old_plan=old_plan,
        new_plan=new_plan,
        session=session,
    )


@login_required
@app.route("/stripe/success")
def stripe_success():
    flash("Your signup was successful. Thank you for supporting AVWX!", "success")
    return redirect(url_for("manage"))


@login_required
@app.route("/stripe/cancel")
def stripe_cancel():
    flash("It looks like you cancelled signup. No changes have been made", "info")
    return redirect(url_for("manage"))


@app.route("/stripe/fulfill", methods=["POST"])
def stripe_fulfill():
    signiture = request.headers.get("Stripe-Signature")
    try:
        event = plans.get_event(request.data, signiture)
    except (ValueError, SignatureVerificationError):
        return "", 400
    if event["type"] == "checkout.session.completed":
        plans.new_subscription(event["data"]["object"])
        return "", 200
    return "", 400


@app.route("/update-card", methods=["GET", "POST"])
@login_required
def update_card():
    if not current_user.customer_id:
        flash("You have no existing card on file", "info")
        return redirect(url_for("manage"))
    if request.method == "POST":
        if plans.update_card(request.form["stripeToken"]):
            flash("Your card has been updated", "success")
        else:
            flash("Something went wrong while updating your card", "error")
        return redirect(url_for("manage"))
    return render_template("update_card.html", stripe_key=app.config["STRIPE_PUB_KEY"])


@app.route("/token")
@login_required
def generate_token():
    if current_user.new_token():
        db.session.commit()
        flash(
            "Your new API token is now active. It may take up to <b>15 minutes</b> for refreshed keys to be valid in the API",
            "success",
        )
    else:
        flash("Your API token has been disabled. Contact michael@mdupont.com", "error")
    return redirect(url_for("manage"))
