"""
Remove accounts that haven't confirmed their email recently
"""

from datetime import datetime, timedelta, timezone
from os import environ
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mdb = MongoClient(environ["MONGO_URI"])
cutoff = timedelta(days=7)


def main() -> int:
    """Remove accounts that haven't confirmed their email recently"""
    now = datetime.now(tz=timezone.utc)
    count = 0
    for user in mdb.account.user.find(
        {"email_confirmed_at": {"$exists": 0}}, {"_id": 1, "email": 1}
    ):
        oid = user["_id"]
        if now - oid.generation_time > cutoff:
            count += 1
            mdb.account.user.delete_one({"_id": oid})
    print(count)
    return 0


if __name__ == "__main__":
    main()
