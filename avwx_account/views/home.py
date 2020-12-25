"""
App home and meta views
"""

# pylint: disable=missing-function-docstring

# library
from flask import render_template
from flask_user import login_required, current_user

# app
from avwx_account import app
from avwx_account.plans import Plan


@app.route("/")
def home():
    return render_template("index.html", plan=getattr(current_user, "plan", None))


@app.route("/manage")
@login_required
def manage():
    if not current_user.plan:
        current_user.plan = Plan.by_key("free").as_embedded()
        current_user.save()
    return render_template(
        "manage.html",
        plan=current_user.plan,
        invoices=current_user.invoices(),
    )


@app.route("/.well-known/apple-developer-merchantid-domain-association")
def apple_pay_mid():
    return app.send_static_file("apple-developer-merchantid-domain-association.dms")
