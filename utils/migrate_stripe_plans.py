"""
Migrate subscription prices to new Stripe products
"""

import re
from os import environ
import stripe
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mdb = MongoClient(environ["MONGO_URI"])
stripe.api_key = environ["STRIPE_SECRET_KEY"]

match = re.compile("^plan_", re.IGNORECASE)


def fetch_plans() -> dict[str, str]:
    """Fetch current plan IDs"""
    plans = mdb.account.plan.find(
        {"stripe_id": {"$exists": 1}}, {"_id": 0, "stripe_id": 1, "name": 1}
    )
    return {p["name"]: p["stripe_id"] for p in plans}


PLAN_NAMES = {
    "Enterprise Monthly": "Enterprise",
    "Pro Yearly": "Pro Yearly",
    "Enterprise Yearly": "Enterprise Yearly",
    "Basic Monthly": "Professional",
}


def migrate_stripe_plan() -> int:
    """Migrate subscription prices to new Stripe products"""
    plans = fetch_plans()
    for user in mdb.account.user.find(
        {"stripe.subscription_id": {"$exists": 1}, "plan.stripe_id": match},
        {"_id": 0, "email": 1, "stripe.subscription_id": 1, "plan.stripe_id": 1},
    ):
        print(user)
        sub_id = user["stripe"]["subscription_id"]
        sub = stripe.Subscription.retrieve(sub_id)
        item = sub["items"]["data"][0]
        new_plan = plans[PLAN_NAMES[item["plan"]["nickname"]]]
        print(new_plan)
        stripe.SubscriptionItem.modify(
            item["id"], price=new_plan, proration_behavior="create_prorations"
        )
        mdb.account.user.update_one(
            {"email": user["email"]}, {"$set": {"plan.stripe_id": new_plan}}
        )
    return 0


if __name__ == "__main__":
    migrate_stripe_plan()
