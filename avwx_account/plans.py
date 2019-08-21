"""
Stripe subscription and customer management
"""

import stripe
from flask_user import current_user
from avwx_account import app, db
from avwx_account.models import Plan, User

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

_ROOT = app.config["ROOT_URL"]
_SESSION = {
    "payment_method_types": ["card"],
    "success_url": _ROOT + "/stripe/success",
    "cancel_url": _ROOT + "/stripe/cancel",
}


def get_session(plan: Plan) -> stripe.checkout.Session:
    """
    Creates a Stripe Session object to start a Checkout
    """
    params = {
        "client_reference_id": current_user.id,
        "subscription_data": {"items": [{"plan": plan.stripe_id}]},
        **_SESSION,
    }
    if current_user.customer_id:
        params["customer"] = current_user.customer_id
    else:
        params["customer_email"] = current_user.email
        params["subscription_data"]["trial_period_days"] = 14
    return stripe.checkout.Session.create(**params)


def get_event(payload: dict, sig: str) -> stripe.api_resources.event.Event:
    """
    Validates a Stripe event to weed out hacked calls
    """
    return stripe.Webhook.construct_event(
        payload, sig, app.config["STRIPE_SIGN_SECRET"]
    )


def new_subscription(session: dict):
    """
    Create a new subscription for a validated Checkout Session
    """
    user = User.query.get(session["client_reference_id"])
    user.customer_id = session["customer"]
    user.subscription_id = session["subscription"]
    plan_id = session["display_items"][0]["plan"]["id"]
    user.plan = Plan.by_stripe_id(plan_id)
    db.session.commit()


def change_subscription(plan: Plan) -> bool:
    """
    Change the subscription from one plan to another
    """
    sub_id = current_user.subscription_id
    if not sub_id or current_user.plan == plan:
        return False
    sub = stripe.Subscription.retrieve(sub_id)
    sub.modify(
        sub_id,
        cancel_at_period_end=False,
        items=[{"id": sub["items"]["data"][0].id, "plan": plan.stripe_id}],
    )
    current_user.subscription_id = sub.id
    current_user.plan = plan
    db.session.commit()
    return True


def cancel_subscription() -> bool:
    """
    Cancel a subscription
    """
    if current_user.subscription_id:
        sub = stripe.Subscription.retrieve(current_user.subscription_id)
        sub.delete()
        current_user.subscription_id = None
    current_user.plan = Plan.by_key("free")
    db.session.commit()
    return True
