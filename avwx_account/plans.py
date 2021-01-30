"""
Stripe subscription and customer management
"""

import stripe
from flask_user import current_user
from avwx_account import app
from avwx_account.models import Plan, Stripe, User

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

_ROOT = app.config["ROOT_URL"]
_SESSION = {
    "payment_method_types": ["card"],
    "success_url": _ROOT + "/stripe/success",
    "cancel_url": _ROOT + "/stripe/cancel",
}


def get_session(plan: Plan) -> stripe.checkout.Session:
    """Creates a Stripe Session object to start a Checkout"""
    params = {
        "client_reference_id": current_user.id,
        "subscription_data": {"items": [{"plan": plan.stripe_id}]},
        **_SESSION,
    }
    if current_user.stripe:
        params["customer"] = current_user.stripe.customer_id
    else:
        params["customer_email"] = current_user.email
    return stripe.checkout.Session.create(**params)


def get_event(payload: dict, sig: str) -> stripe.api_resources.event.Event:
    """Validates a Stripe event to weed out hacked calls"""
    return stripe.Webhook.construct_event(
        payload, sig, app.config["STRIPE_SIGN_SECRET"]
    )


def new_subscription(session: dict) -> bool:
    """Create a new subscription for a validated Checkout Session"""
    user = User.objects(id=session["client_reference_id"]).first()
    if user is None:
        return False
    user.stripe = Stripe(
        customer_id=session["customer"], subscription_id=session["subscription"]
    )
    plan_id = session["display_items"][0]["plan"]["id"]
    user.plan = Plan.by_stripe_id(plan_id).as_embedded()
    user.new_token(dev=True)
    user.save()
    return True


def change_subscription(plan: Plan) -> bool:
    """Change the subscription from one plan to another"""
    if not current_user.stripe:
        return False
    sub_id = current_user.stripe.subscription_id
    if not sub_id or current_user.plan == plan:
        return False
    sub = stripe.Subscription.retrieve(sub_id)
    sub.modify(
        sub_id,
        cancel_at_period_end=False,
        items=[{"id": sub["items"]["data"][0].id, "plan": plan.stripe_id}],
    )
    current_user.stripe.subscription_id = sub.id
    current_user.plan = plan
    current_user.save()
    return True


def cancel_subscription() -> bool:
    """Cancel a subscription"""
    if not current_user.stripe:
        return False
    if current_user.stripe.subscription_id:
        sub = stripe.Subscription.retrieve(current_user.stripe.subscription_id)
        sub.delete()
        current_user.stripe.subscription_id = None
    current_user.plan = Plan.by_key("free").as_embedded()
    current_user.remove_token_by(type="dev")
    current_user.save()
    return True


# def update_card(token: str) -> bool:
#     """Update stored credit card based on returned Stripe token"""
#     if not current_user.stripe.customer_id:
#         return False
#     stripe.Customer.modify(current_user.stripe.customer_id, source=token)
#     return True
