"""
Adds paid accounts to mailing list
"""

from os import environ
from dotenv import load_dotenv
from mailchimp3 import MailChimp
from pymongo import MongoClient

load_dotenv()

mdb = MongoClient(environ["MONGO_URI"])
mc = MailChimp(mc_api=environ["MC_KEY"], mc_user=environ["MC_USERNAME"])
LIST_ID = environ["MC_LIST_ID"]


def main() -> int:
    """Adds paid accounts to mailing list"""
    count = 0
    for user in mdb.account.user.find(
        {"plan.type": {"$ne": "free"}}, {"_id": 1, "email": 1, "plan.type": 1}
    ):
        if user.get("plan") is None:
            continue
        data = {"email_address": user["email"], "status": "subscribed"}
        try:
            mc.lists.members.create(LIST_ID, data)
            mdb.account.user.update_one(
                {"_id": user["_id"]}, {"$set": {"subscribed": True}}
            )
            count += 1
        except Exception as exc:
            print(exc)
    print(count)
    return 0


if __name__ == "__main__":
    main()
