"""
Add token_id to token usage collection
"""

from os import environ
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mdb = MongoClient(environ["MONGO_URI"])


def main() -> int:
    """
    Add token_id to token usage collection
    """
    mdb.account.user.f
    for user in mdb.account.user.find({"tokens": {"$exists": 1}}, {"tokens": 1}):
        print(user)
        tokens = [t for t in user["tokens"] if t["type"] == "app"]
        if not tokens:
            continue
        token = tokens[0]
        resp = mdb.account.token.update_many(
            {"user_id": user["_id"]},
            {"$set": {"token_id": token["_id"]}},
        )
        print(resp.modified_count)
    return 0


if __name__ == "__main__":
    main()
