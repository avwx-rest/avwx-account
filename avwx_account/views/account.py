"""
Account management views
"""

# library
from flask import flash, redirect, render_template, request, url_for
from flask_login import logout_user
from flask_user import login_required, current_user

# app
import avwx_account.mail as mail
from avwx_account import app, plans


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    email = ""
    if request.method == "POST":
        email = request.form["email"]
        if email == current_user.email:
            plans.cancel_subscription()
            mail.delete_from_mailing_list(email)
            current_user.delete()
            logout_user()
            flash("Your account has been deleted", "success")
            return redirect(url_for("home"))
        flash("Email does not match", "error")
    return render_template("delete_account.html", form_email=email)


@app.route("/subscribe")
@login_required
def subscribe():
    if not current_user.subscribed:
        msg = mail.add_to_mailing_list(current_user.email)
        if msg is None:
            current_user.subscribed = True
            current_user.save()
    else:
        msg = "You have already subscribed"
    flash(msg or "Added to the mailing list", "info")
    return redirect(url_for("manage"))
