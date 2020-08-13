"""
App routing and view logic
"""

# stdlib
import hashlib

# library
import rollbar
from flask import flash, redirect, render_template, request, url_for
from flask_login import logout_user
from flask_user import login_required, current_user
from mailchimp3.mailchimpclient import MailChimpError
from stripe.error import SignatureVerificationError

# app
from avwx_account import app, mc, plans


@app.route("/")
def home():
    return render_template("index.html", plan=getattr(current_user, "plan", None))


@app.route("/manage")
@login_required
def manage():
    if not current_user.plan:
        current_user.plan = plans.Plan.by_key("free").as_embedded()
        current_user.save()
    return render_template(
        "manage.html",
        plan=current_user.plan,
        invoices=current_user.invoices(),
        # token_counts=current_user.token_usage(),
    )


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    email = ""
    if request.method == "POST":
        email = request.form["email"]
        if email == current_user.email:
            plans.cancel_subscription()
            try:
                target = hashlib.md5(email.encode("utf-8")).hexdigest()
                mc.lists.members.delete(app.config.get("MC_LIST_ID"), target)
            except MailChimpError as exc:
                data = exc.args[0]
                # if data.get("title") != "Member Exists":
                rollbar.report_message(data)
            current_user.delete()
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
    new_plan = plans.Plan.by_key(plan).as_embedded()
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
    if new_plan.price:
        if current_user.stripe is None or not current_user.stripe.subscription_id:
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
    flash("Your sign-up was successful. Thank you for supporting AVWX!", "success")
    return redirect(url_for("manage"))


@login_required
@app.route("/stripe/cancel")
def stripe_cancel():
    flash("It looks like you cancelled sign-up. No changes have been made", "info")
    return redirect(url_for("manage"))


@app.route("/stripe/fulfill", methods=["POST"])
def stripe_fulfill():
    signature = request.headers.get("Stripe-Signature")
    try:
        event = plans.get_event(request.data, signature)
    except (ValueError, SignatureVerificationError):
        return "", 400
    if event["type"] == "checkout.session.completed":
        plans.new_subscription(event["data"]["object"])
        return "", 200
    return "", 400


@app.route("/update-card", methods=["GET", "POST"])
@login_required
def update_card():
    if not current_user.stripe.customer_id:
        flash("You have no existing card on file", "info")
        return redirect(url_for("manage"))
    if request.method == "POST":
        if plans.update_card(request.form["stripeToken"]):
            flash("Your card has been updated", "success")
        else:
            flash("Something went wrong while updating your card", "error")
        return redirect(url_for("manage"))
    return render_template("update_card.html", stripe_key=app.config["STRIPE_PUB_KEY"])


@app.route("/token/new")
@login_required
def new_token():
    if current_user.new_token():
        current_user.save()
    else:
        flash("Your API token has been disabled. Contact michael@mdupont.com", "error")
    return redirect(url_for("manage"))


@app.route("/token/edit", methods=["GET", "POST"])
@login_required
def edit_token():
    token = current_user.get_token(request.args.get("value"))
    if token is None:
        flash("Token not found in your account", "error")
        return redirect(url_for("manage"))
    if request.method == "POST":
        print(request.form)
        if current_user.update_token(
            token.value,
            name=request.form.get("name", "App"),
            active=bool(request.form.get("active")),
        ):
            current_user.save()
            return redirect(url_for("manage"))
        else:
            flash("Your token was not able to be updated", "error")
    return render_template("edit_token.html", token=token)


@app.route("/token/refresh")
def refresh_token():
    token = current_user.get_token(request.args.get("value"))
    if token is None:
        flash("Token not found in your account", "error")
        return redirect(url_for("manage"))
    current_user.refresh_token(token.value)
    current_user.save()
    return redirect(url_for("manage"))


@app.route("/token/delete")
def delete_token():
    token = current_user.get_token(request.args.get("value"))
    if token is None:
        flash("Token not found in your account", "error")
    elif token.type == "dev":
        flash("Cannot delete a development token. Disable instead", "error")
    else:
        current_user.remove_token_by(value=token.value)
        current_user.save()
    return redirect(url_for("manage"))


# @app.route("/token/usage")
# def delete_token():
#     token = current_user.get_token(request.args.get("value"))
#     if token is None:
#         flash("Token not found in your account", "error")
#         return redirect(url_for("manage"))
#     current_user.remove_token_usage(value=token.value)
#     current_user.save()
#     return render_template("token_usage.html", token_counts=token_counts)


@app.route("/.well-known/apple-developer-merchantid-domain-association")
def apple_pay_mid():
    return app.send_static_file("apple-developer-merchantid-domain-association.dms")
