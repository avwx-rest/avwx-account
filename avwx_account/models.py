"""
Manages database models
"""

# stdlib
from secrets import token_urlsafe

# library
import stripe
from flask_user import UserMixin
from sqlalchemy.sql import func

# module
from avwx_account import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    active = db.Column("is_active", db.Boolean(), nullable=False, server_default="1")

    email = db.Column(db.String(255), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default="")

    # User information
    first_name = db.Column(db.String(100), nullable=False, server_default="")
    last_name = db.Column(db.String(100), nullable=False, server_default="")

    # API and Payment information
    customer_id = db.Column(db.String(32), nullable=True)
    subscription_id = db.Column(db.String(32), nullable=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"))
    plan = db.relationship("Plan")
    apitoken = db.Column(db.String(43), nullable=True, server_default="")
    active_token = db.Column(db.Boolean(), nullable=False, server_default="0")

    # Define the relationship to Role via UserRoles
    roles = db.relationship(
        "Role", secondary="user_roles", backref=db.backref("users", lazy="dynamic")
    )

    def __repr__(self) -> str:
        return f"<User ({self.id}) {self.email}>"

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.email == other.email
        return False

    def new_token(self) -> bool:
        """
        Generate a new API token
        """
        if self.apitoken and not self.active_token:
            return False
        self.apitoken = token_urlsafe(32)
        self.active_token = True
        return True

    def clear_token(self):
        """
        Clears an active token
        """
        self.apitoken = None
        self.active_token = False

    @classmethod
    def by_email(cls, email: str) -> "User":
        return cls.query.filter(cls.email == email).first()

    @classmethod
    def by_customer_id(cls, id: str) -> "User":
        return cls.query.filter(cls.customer_id == id).first()

    @property
    def stripe_data(self) -> stripe.Customer:
        try:
            if self.customer_id:
                return stripe.Customer.retrieve(self.customer_id)
        except stripe.error.InvalidRequestError:
            pass
        return

    def invoices(self, limit: int = 5) -> list:
        """
        Returns the user's recent invoice objects
        """
        try:
            if self.customer_id:
                return stripe.Invoice.list(customer=self.customer_id, limit=limit)[
                    "data"
                ]
        except stripe.error.InvalidRequestError:
            pass
        return


class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self) -> str:
        return f"<Role {self.name}>"

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)


user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id", ondelete="CASCADE")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id", ondelete="CASCADE")),
)


class Plan(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(32))
    type = db.Column(db.String(32))
    stripe_id = db.Column(db.String(20), nullable=True)
    description = db.Column(db.String(64))
    price = db.Column(db.SmallInteger())
    level = db.Column(db.SmallInteger())
    limit = db.Column(db.Integer())

    def __repr__(self) -> str:
        return f"<Plan {self.key}>"

    def __str__(self) -> str:
        return self.key

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other) -> bool:
        if not other:
            return False
        if isinstance(other, str):
            return self.key == other
        return self.key == other.key

    def __lt__(self, other) -> bool:
        if other is None:
            return False
        if isinstance(other, int):
            return self.level < other
        return self.level < other.level

    def __gt__(self, other) -> bool:
        if other is None:
            return True
        if isinstance(other, int):
            return self.level > other
        return self.level > other.level

    @classmethod
    def by_key(cls, key: str) -> "Plan":
        return cls.query.filter(cls.key == key).first()

    @classmethod
    def by_stripe_id(cls, id: str) -> "Plan":
        return cls.query.filter(cls.stripe_id == id).first()
