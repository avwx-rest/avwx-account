"""
"""

from flask import render_template_string
from flask_user import UserManager, login_required, roles_required
from avwx_account import app, db
from avwx_account.models import User

user_manager = UserManager(app, db, User)

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    return render_template_string("""
        {% extends "flask_user_layout.html" %}
        {% block content %}
            <h2>Home page</h2>
            <p><a href={{ url_for('user.register') }}>Register</a></p>
            <p><a href={{ url_for('user.login') }}>Sign in</a></p>
            <p><a href={{ url_for('home_page') }}>Home Page</a> (accessible to anyone)</p>
            <p><a href={{ url_for('member_page') }}>Member Page</a> (login_required: member@example.com / Password1)</p>
            <p><a href={{ url_for('admin_page') }}>Admin Page</a> (role_required: admin@example.com / Password1')</p>
            <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
        {% endblock %}
        """)

# The Members page is only accessible to authenticated users
@app.route('/members')
@login_required    # Use of @login_required decorator
def member_page():
    return render_template_string("""
        {% extends "flask_user_layout.html" %}
        {% block content %}
            <h2>Members page</h2>
            <p><a href={{ url_for('user.register') }}>Register</a></p>
            <p><a href={{ url_for('user.login') }}>Sign in</a></p>
            <p><a href={{ url_for('home_page') }}>Home Page</a> (accessible to anyone)</p>
            <p><a href={{ url_for('member_page') }}>Member Page</a> (login_required: member@example.com / Password1)</p>
            <p><a href={{ url_for('admin_page') }}>Admin Page</a> (role_required: admin@example.com / Password1')</p>
            <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
        {% endblock %}
        """)

# The Admin page requires an 'Admin' role.
@app.route('/admin')
@roles_required('Admin')
def admin_page():
    return render_template_string("""
        {% extends "flask_user_layout.html" %}
        {% block content %}
            <h2>Admin Page</h2>
            <p><a href={{ url_for('user.register') }}>Register</a></p>
            <p><a href={{ url_for('user.login') }}>Sign in</a></p>
            <p><a href={{ url_for('home_page') }}>Home Page</a> (accessible to anyone)</p>
            <p><a href={{ url_for('member_page') }}>Member Page</a> (login_required: member@example.com / Password1)</p>
            <p><a href={{ url_for('admin_page') }}>Admin Page</a> (role_required: admin@example.com / Password1')</p>
            <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
        {% endblock %}
        """)