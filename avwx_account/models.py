"""
Manages database models
"""

# stdlib
from datetime import datetime
from secrets import token_urlsafe
from typing import Optional

# library
import stripe as stripelib
from bson import ObjectId
from flask_user import UserMixin

# module
from avwx_account import db, mdb


class Stripe(db.EmbeddedDocument):
    customer_id = db.StringField()
    subscription_id = db.StringField()


class Token(db.EmbeddedDocument):
    _id = db.ObjectIdField()
    name = db.StringField()
    type = db.StringField()
    value = db.StringField()
    active = db.BooleanField(default=True)

    @property
    def is_unique(self) -> bool:
        resp = mdb.account.user.find_one({"tokens.value": self.value}, {"_id": 1})
        return resp is None

    def _gen(self):
        value = token_urlsafe(32)
        if self.type == "dev":
            value = "dev-" + value[4:]
        self.value = value

    @classmethod
    def new(cls, name: str = "Token", type: str = "app"):
        """
        Generate a new unique token
        """
        token = cls(_id=ObjectId(), name=name, type=type, value="")
        token.refresh()
        return token

    @classmethod
    def dev(cls):
        """
        Generate a new development token
        """
        return cls.new("Development", "dev")

    def refresh(self):
        """
        Refresh the token value
        """
        self._gen()
        while not self.is_unique:
            self._gen()


class PlanBase:
    key = db.StringField()
    name = db.StringField()
    type = db.StringField()
    stripe_id = db.StringField()
    description = db.StringField()
    price = db.IntField()
    level = db.IntField()
    limit = db.IntField()

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


class PlanEmbedded(db.EmbeddedDocument, PlanBase):
    pass


class Plan(db.Document, PlanBase):

    key = db.StringField(unique=True)

    @classmethod
    def by_key(cls, key: str) -> "Plan":
        return cls.objects(key=key).first()

    @classmethod
    def by_stripe_id(cls, id: str) -> "Plan":
        return cls.objects(stripe_id=id).first()

    def as_embedded(self) -> PlanEmbedded:
        return PlanEmbedded(
            key=self.key,
            name=self.name,
            type=self.type,
            stripe_id=self.stripe_id,
            description=self.description,
            price=self.price,
            level=self.level,
            limit=self.limit,
        )


class User(db.Document, UserMixin):
    active = db.BooleanField(default=False)
    disabled = db.BooleanField(default=False)
    old_id = db.IntField()

    email = db.EmailField(unique=True)
    email_confirmed_at = db.DateTimeField()
    password = db.StringField()

    # User information
    first_name = db.StringField()
    last_name = db.StringField()

    # API and Payment information
    stripe = db.EmbeddedDocumentField(Stripe)
    plan = db.EmbeddedDocumentField(PlanEmbedded)
    token = db.EmbeddedDocumentField(Token)
    tokens = db.ListField(db.EmbeddedDocumentField(Token), default=[])

    roles = db.ListField(db.StringField(), default=[])

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.email == other.email
        return False

    def new_token(self, dev: bool = False) -> bool:
        """
        Generate a new API token
        """
        if self.disabled:
            return False
        if dev:
            for token in self.tokens:
                if token.type == "dev":
                    return False
            token = Token.dev()
        else:
            token = Token.new()
        self.tokens.append(token)
        return True

    def get_token(self, value: str) -> Optional[str]:
        """
        Returns a Token matching the token value
        """
        for token in self.tokens:
            if value and token.value == value:
                return token
        return None

    def update_token(self, value: str, name: str, active: bool) -> bool:
        """
        Update certain fields on a Token matching a token value
        """
        for i, token in enumerate(self.tokens):
            if value and token.value == value:
                self.tokens[i].name = name
                self.tokens[i].active = active
                return True
        return False

    def refresh_token(self, value: str):
        """
        Create a new Token value
        """
        for i, token in enumerate(self.tokens):
            if value and token.value == value:
                self.tokens[i].refresh()

    # def token_usage(self, limit: int = 5) -> Dict[datetime, int]:
    #     """
    #     Returns recent token usage counts
    #     """
    #     if not (self.token and self.token.active):
    #         return
    #     data = mdb.account.token.aggregate(
    #         [
    #             {"$match": {"user_id": self.id}},
    #             {"$project": {"_id": 0, "date": 1, "count": 1}},
    #             {"$sort": {"date": -1}},
    #             {"$limit": limit},
    #         ]
    #     )
    #     return {item["date"]: item["count"] for item in data}

    def remove_token_by(self, value: str = None, type: str = None) -> bool:
        """
        Remove the first token encountered matching a value or type
        """
        for i, token in enumerate(self.tokens):
            if (value and token.value == value) or (type and token.type == type):
                self.tokens.pop(i)
                return True
        return False

    @classmethod
    def by_email(cls, email: str) -> "User":
        return cls.objects(email=email).first()

    @classmethod
    def by_customer_id(cls, id: str) -> "User":
        return cls.objects(stripe__customer_id=id).first()

    @property
    def created(self) -> datetime:
        return self.id.generation_time

    @property
    def stripe_data(self) -> stripelib.Customer:
        try:
            return stripelib.Customer.retrieve(self.stripe.customer_id)
        except AttributeError:
            pass
        except stripelib.error.InvalidRequestError:
            pass

    def invoices(self, limit: int = 5) -> list:
        """
        Returns the user's recent invoice objects
        """
        try:
            return stripelib.Invoice.list(
                customer=self.stripe.customer_id, limit=limit
            )["data"]
        except (AttributeError, stripelib.error.InvalidRequestError):
            pass
