"""
avwx_account.models - Manages database models
"""

# stdlib
from secrets import token_urlsafe
from flask_user import UserManager, UserMixin
from avwx_account import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    email = db.Column(db.String(255), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

    # API and Payment information
    customer_id = db.Column(db.String(32), nullable=True)
    subscription_id = db.Column(db.String(32), nullable=True)
    plan = db.Column(db.String(16), nullable=True)
    apitoken = db.Column(db.String(43), nullable=True, server_default='')
    active_token = db.Column(db.Boolean(), nullable=False, server_default='0')

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email

    def __hash__(self):
        return hash(self.email)

    def new_token(self) -> bool:
        """
        Generate a new API token
        """
        if self.customer_id and self.subscription_id:
            self.apitoken = token_urlsafe(32)
            self.active_token = True
            return True
        return False

    def clear_token(self):
        """
        Clears an active token
        """
        self.apitoken = None
        self.active_token = False

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))
)
