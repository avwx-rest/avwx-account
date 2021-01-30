"""
Payment management and callback views
"""

# library
import stripe
from flask import flash, redirect, request, url_for
from flask_user import login_required, current_user
from stripe.error import SignatureVerificationError

# app
from avwx_account import app, plans


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
        if plans.new_subscription(event["data"]["object"]):
            return "", 200
    return "", 400


# @app.route("/update-card", methods=["GET", "POST"])
# @login_required
# def update_card():
#     if not current_user.stripe.customer_id:
#         flash("You have no existing card on file", "info")
#         return redirect(url_for("manage"))
#     if request.method == "POST":
#         if plans.update_card(request.form["stripeToken"]):
#             flash("Your card has been updated", "success")
#         else:
#             flash("Something went wrong while updating your card", "error")
#         return redirect(url_for("manage"))
#     return render_template("update_card.html", stripe_key=app.config["STRIPE_PUB_KEY"])


@app.route("/create-customer-portal-session")
@login_required
def customer_portal():
    if not current_user.stripe.customer_id:
        flash("You have no existing payment history", "info")
        return redirect(url_for("manage"))
    session = stripe.billing_portal.Session.create(
        customer=current_user.stripe.customer_id,
        return_url=app.config["ROOT_URL"] + "/manage",
    )
    return redirect(session.url)
