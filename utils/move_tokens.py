"""
Move and reformat tokens into account db
"""

# stdlib
from datetime import datetime
from os import environ

# library
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

load_dotenv()


def main() -> int:
    """Move and reformat tokens into account db"""
    mdb = MongoClient(environ["MONGO_URI"])
    for token in mdb.counter.token.find():
        user = mdb.account.user.find_one({"old_id": token["_id"]}, {"_id": 1})
        if not user:
            continue
        del token["_id"]
        counts = [
            UpdateOne(
                {"user_id": user["_id"], "date": datetime.strptime(k, r"%Y-%m-%d")},
                {"$inc": {"count": v}},
                upsert=True,
            )
            for k, v in token.items()
        ]
        mdb.account.token.bulk_write(counts, ordered=False)
    return 0


if __name__ == "__main__":
    main()
