"""
Update a user's plan information
"""

# stdlib
from os import environ

# library
import begin
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


@begin.start
def change_plan(email: str, plan: str) -> int:
    """
    Change a user's plan details

    Does not touch Stripe fields
    """
    mdb = MongoClient(environ["MONGO_URI"])
    plan_data = mdb.account.plan.find_one({"key": plan}, {"_id": 0})
    if not plan_data:
        print(f"No plan found for {plan}")
        return 1
    resp = mdb.account.user.update_one({"email": email}, {"$set": {"plan": plan_data}})
    if not resp.matched_count:
        print(f"No user found for {email}")
    elif not resp.modified_count:
        print(f"{email} is already on {plan_data['name']}")
    else:
        print(f"{email} has been set to {plan_data['name']}")
        return 0
    return 2
