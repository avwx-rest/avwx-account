"""
Copy all users from sql to mongo

Move to root to import mongoengine models
"""

# stdlib
from os import environ
from typing import List

# library
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# module
from avwx_account.models import PlanEmbedded, Token, Stripe, User


USER_FIELDS = {
    "old_id": 0,
    "active": 1,
    "email": 2,
    "email_confirmed_at": 3,
    "password": 4,
    "first_name": 5,
    "last_name": 6,
}

TOKEN_FIELDS = {"active": 7, "value": 8}

STRIPE_FIELDS = {"customer_id": 9, "subscription_id": 10}

PLAN_FIELDS = {
    "key": 1,
    "name": 2,
    "type": 3,
    "stripe_id": 4,
    "description": 5,
    "price": 6,
    "level": 7,
    "limit": 8,
}

PLANS = {}


def fill_model(data: List[str], fields: dict, model: "mongo model") -> "mongo model":
    """Populates a mongo model with SQL query data according to a key map"""
    new_data = {k: data[i] for k, i in fields.items()}
    # Filter out all-null items
    for item in new_data.values():
        if item:
            break
    else:
        return
    return model(**new_data)


def get_plans(cur):
    """Populate the plan embedded dict"""
    cur.execute("SELECT * FROM public.plan;")
    for plan in cur.fetchall():
        PLANS[plan[0]] = fill_model(plan, PLAN_FIELDS, PlanEmbedded)


def handle_user(data: List[str]):
    """Convert user SQL query into a mongo document and save"""
    user = fill_model(data, USER_FIELDS, User)
    user.stripe = fill_model(data, STRIPE_FIELDS, Stripe)
    user.token = fill_model(data, TOKEN_FIELDS, Token)
    user.plan = PLANS.get(data[13])
    user.save()


def main() -> int:
    """Copy all users from sql to mongo"""
    conn = psycopg2.connect(environ.get("SQLALCHEMY_DATABASE_URI"))
    cur = conn.cursor()
    get_plans(cur)
    cur.execute("SELECT * FROM public.user;")
    for user in cur.fetchall():
        handle_user(user)
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    main()
