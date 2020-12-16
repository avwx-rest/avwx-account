"""
Verify a user's email
"""

# stdlib
from datetime import datetime
from os import environ

# library
import begin
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


@begin.start
def change_plan(email: str) -> int:
    """Change a user's plan details"""
    mdb = MongoClient(environ["MONGO_URI"])
    command = {"$set": {"email_verified_at": datetime.utcnow()}}
    resp = mdb.account.user.update_one({"email": email}, command)
    if not resp.matched_count:
        print(f"No user found for {email}")
    elif not resp.modified_count:
        print(f"{email} is already verified")
    else:
        print(f"{email} has been verified")
        return 0
    return 2
