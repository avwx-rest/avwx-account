"""
Cleans unverified users from the database

.env must be loaded to run:
`set -o allexport; source .env; set +o allexport`
"""

# stdlib
from datetime import datetime, timedelta, timezone

# module
from avwx_account import db
from avwx_account.models import User


def main() -> int:
    """
    Delete users with unverified emails older than 30 days
    """
    users = db.session.query(User).filter(User.email_confirmed_at == None)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    changed = False
    for user in users:
        if user.created < cutoff:
            db.session.delete(user)
            changed = True
    if changed:
        db.session.commit()
    return 0


if __name__ == "__main__":
    main()
