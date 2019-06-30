"""
Stripe subscription and customer management
"""

import stripe
from flask_user import current_user
from avwx_account import app, db
from avwx_account.models import Plan

stripe.api_key = app.config["STRIPE_SECRET_KEY"]


def get_plan(plan: str) -> Plan:
    """
    Returns a plan by key or None if key not found
    """
    return Plan.query.filter(Plan.key == plan).first()


def get_customer_id(token: str = None) -> str:
    """
    Fetch a customer ID by database lookup or create one if a token is provided
    """
    cid = current_user.customer_id
    if not cid and token:
        cid = stripe.Customer.create(email=current_user.email, source=token).id
        current_user.customer_id = cid
        db.session.commit()
    return cid


def new_subscription(plan: Plan, token: str) -> bool:
    """
    Create a new subscription for the current user
    """
    if plan.stripe_id:
        customer_id = get_customer_id(token)
        subscription = stripe.Subscription.create(
            customer=customer_id, items=[{"plan": plan.stripe_id}]
        )
        current_user.subscription_id = subscription.id
    current_user.plan = plan
    db.session.commit()
    return True


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
    current_user.plan = get_plan("free")
    db.session.commit()
    return True
