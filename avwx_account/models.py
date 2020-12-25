"""
Manages database models
"""

# stdlib
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Dict, List, Optional

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
        """Generate a new unique token"""
        token = cls(_id=ObjectId(), name=name, type=type, value="")
        token.refresh()
        return token

    @classmethod
    def dev(cls):
        """Generate a new development token"""
        return cls.new("Development", "dev")

    def refresh(self):
        """Refresh the token value"""
        self._gen()
        while not self.is_unique:
            self._gen()


class PlanBase:
    meta = {"strict": False}

    key = db.StringField()
    name = db.StringField()
    type = db.StringField()
    stripe_id = db.StringField()
    description = db.StringField()
    price = db.IntField()
    level = db.IntField()
    limit = db.IntField()
    overage = db.BooleanField(default=False)

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
    meta = {"strict": False}

    active = db.BooleanField(default=False)
    disabled = db.BooleanField(default=False)

    email = db.EmailField(unique=True)
    email_confirmed_at = db.DateTimeField()
    password = db.StringField()

    # User information
    first_name = db.StringField()
    last_name = db.StringField()

    # API and Payment information
    stripe = db.EmbeddedDocumentField(Stripe)
    plan = db.EmbeddedDocumentField(PlanEmbedded)
    tokens = db.ListField(db.EmbeddedDocumentField(Token), default=[])
    allow_overage = db.BooleanField(default=False)

    subscribed = db.BooleanField(default=False)
    roles = db.ListField(db.StringField(), default=[])

    _token_cache = None
    _update_cache_at = None

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
        """Generate a new API token"""
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

    def get_token(
        self, value: Optional[str] = None, _id: Optional[ObjectId] = None
    ) -> Optional[str]:
        """Returns a Token matching the token value or id"""
        for token in self.tokens:
            if value and token.value == value:
                return token
            if _id and token._id == _id:
                return token
        return None

    def update_token(self, value: str, name: str, active: bool) -> bool:
        """Update certain fields on a Token matching a token value"""
        for i, token in enumerate(self.tokens):
            if value and token.value == value:
                self.tokens[i].name = name
                self.tokens[i].active = active
                return True
        return False

    def refresh_token(self, value: str):
        """Create a new Token value"""
        for i, token in enumerate(self.tokens):
            if value and token.value == value:
                self.tokens[i].refresh()

    @property
    def _should_use_cache(self) -> bool:
        if not self._token_cache:
            return False
        if len(self._token_cache) != len(self.tokens):
            return False
        return datetime.now(tz=timezone.utc) > self._update_cache_at

    def token_usage(
        self, limit: int = 30, refresh: bool = False
    ) -> Dict[ObjectId, dict]:
        """Returns recent token usage counts"""
        if not self.tokens:
            return {}
        if not refresh and self._should_use_cache:
            return self._token_cache
        target = datetime.now(tz=timezone.utc) - timedelta(days=limit)
        data = mdb.account.token.aggregate(
            [
                {"$match": {"user_id": self.id, "date": {"$gte": target}}},
                {"$project": {"_id": 0, "date": 1, "count": 1, "token_id": 1}},
                {
                    "$group": {
                        "_id": "$date",
                        "counts": {
                            "$push": {"token_id": "$token_id", "count": "$count"}
                        },
                    }
                },
            ]
        )
        data = {
            i["_id"].date(): {j["token_id"]: j["count"] for j in i["counts"]}
            for i in data
        }
        days = [(target + timedelta(days=i)).date() for i in range(limit)]
        app_tokens = {t._id: [] for t in self.tokens if t.type != "dev"}
        dev_tokens = {t._id: [] for t in self.tokens if t.type == "dev"}
        for day in days:
            tokens = data.get(day, {})
            for token_id in app_tokens:
                app_tokens[token_id].append(tokens.get(token_id, 0))
            for token_id in dev_tokens:
                dev_tokens[token_id].append(tokens.get(token_id, 0))
        ret = {"days": days, "app": app_tokens, "dev": dev_tokens}
        ret["total"] = [sum(i) for i in zip(*app_tokens.values())]
        self._token_cache = ret
        self._update_cache_at = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
        return ret

    def remove_token_by(self, value: str = None, type: str = None) -> bool:
        """Remove the first token encountered matching a value or type"""
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
    def stripe_data(self) -> Optional[stripelib.Customer]:
        with suppress(AttributeError, stripelib.error.InvalidRequestError):
            return stripelib.Customer.retrieve(self.stripe.customer_id)

    def invoices(self, limit: int = 5) -> List[dict]:
        """Returns the user's recent invoice objects"""
        with suppress(AttributeError, stripelib.error.InvalidRequestError):
            return stripelib.Invoice.list(
                customer=self.stripe.customer_id, limit=limit
            )["data"]
        return []
