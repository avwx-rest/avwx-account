"""
Cleans unverified users from the database
"""

# stdlib
from datetime import datetime, timedelta, timezone

# library
from dotenv import load_dotenv

# module
from avwx_account.models import User


def main() -> int:
    """
    Delete users with unverified emails older than 30 days
    """
    users = User.objects(email_confirmed_at=None)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    for user in users:
        if user.created < cutoff:
            user.delete()
    return 0


if __name__ == "__main__":
    load_dotenv()
    main()
