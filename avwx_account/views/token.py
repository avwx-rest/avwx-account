"""
Token management views
"""

# library
from flask import flash, redirect, render_template, request, url_for
from flask_user import login_required, current_user

# app
from avwx_account import app


@app.route("/token/new")
@login_required
def new_token():
    if current_user.new_token():
        current_user.save()
    else:
        flash("Your account has been disabled. Contact avwx@dupont.dev", "error")
    return redirect(url_for("manage"))


@app.route("/token/edit", methods=["GET", "POST"])
@login_required
def edit_token():
    token = current_user.get_token(request.args.get("value"))
    if token is None:
        flash("Token not found in your account", "error")
        return redirect(url_for("manage"))
    if request.method == "POST":
        if current_user.update_token(
            token.value,
            name=request.form.get("name", "App"),
            active=bool(request.form.get("active")),
        ):
            current_user.save()
            return redirect(url_for("manage"))
        flash("Your token was not able to be updated", "error")
    return render_template("edit_token.html", token=token)


@app.route("/token/refresh")
@login_required
def refresh_token():
    token = current_user.get_token(request.args.get("value"))
    if token is None:
        flash("Token not found in your account", "error")
        return redirect(url_for("manage"))
    current_user.refresh_token(token.value)
    current_user.save()
    return redirect(url_for("manage"))


@app.route("/token/delete")
@login_required
def delete_token():
    token = current_user.get_token(request.args.get("value"))
    if token is None:
        flash("Token not found in your account", "error")
    elif token.type == "dev":
        flash("Cannot delete a development token. Disable instead", "error")
    else:
        current_user.remove_token_by(value=token.value)
        current_user.save()
    return redirect(url_for("manage"))
