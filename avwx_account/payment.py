import stripe
from flask_user import current_user
from avwx_account import app, db

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

PLANS = {
    "basic": {
        "id": app.config["STRIPE_BASIC_ID"],
        "description": "AVWX Basic Monthly",
        "price": 10,
    },
    "enterprise": {
        "id": app.config["STRIPE_ENTERPRISE_ID"],
        "description": "AVWX Enterprise Monthly",
        "price": 40,
    },
}


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


def new_subscription(plan: str, token: str) -> bool:
    """
    Create a new subscription for the current user
    """
    cid = get_customer_id(token)
    subscription = stripe.Subscription.create(
        customer=cid, items=[{"plan": PLANS[plan]["id"]}]
    )
    current_user.subscription_id = subscription.id
    current_user.plan = plan
    db.session.commit()
    return True


def change_subscription(plan: str) -> bool:
    """
    Change the subscription from one plan to another
    """
    sid = current_user.subscription_id
    if not sid or current_user.plan == plan:
        return False
    subscription = stripe.Subscription.retrieve(sid)
    subscription.modify(
        sid,
        cancel_at_period_end=False,
        items=[{"id": subscription["items"]["data"][0].id, "plan": PLANS[plan]["id"]}],
    )
    current_user.subscription_id = subscription.id
    current_user.plan = plan
    db.session.commit()
    return True


def cancel_subscription() -> bool:
    """
    Cancel a subscription
    """
    sid = current_user.subscription_id
    if sid:
        subscription = stripe.Subscription.retrieve(sid)
        subscription.delete()
    cid = current_user.customer_id
    if cid:
        customer = stripe.Customer.retrieve(cid)
        customer.delete()
    current_user.customer_id = None
    current_user.subscription_id = None
    current_user.plan = None
    db.session.commit()
    return True
