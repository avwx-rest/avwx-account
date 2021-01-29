"""
Plan management views
"""

# library
from flask import flash, redirect, render_template, request, url_for
from flask_user import login_required, current_user

# app
from avwx_account import app, plans


@app.route("/change/<plan>", methods=["GET", "POST"])
@login_required
def change(plan: str):
    new_plan = plans.Plan.by_key(plan).as_embedded()
    if new_plan is None:
        return redirect(url_for("manage"))
    if current_user.plan == new_plan:
        flash(f"You are already subscribed to the {new_plan.name} plan", "info")
        return redirect(url_for("manage"))
    old_plan = current_user.plan
    session = None
    if request.method == "POST":
        msg = f"Your {new_plan.name} plan is now active"
        if new_plan.price:
            if not plans.change_subscription(new_plan):
                flash("Unable to update your subscription", "error")
                return redirect(url_for("manage"))
            msg += ". Thank you for supporting AVWX!"
        else:
            plans.cancel_subscription()
        flash(msg, "success")
        return redirect(url_for("manage"))
    if new_plan.price:
        if current_user.stripe is None or not current_user.stripe.subscription_id:
            session = plans.get_session(new_plan)
    return render_template(
        "change.html",
        stripe_key=app.config["STRIPE_PUB_KEY"],
        old_plan=old_plan,
        new_plan=new_plan,
        session=session,
    )


# Disabled because Stripe Checkout can't accept a standalone metered item
# @app.route("/plan/overage/new")
# @login_required
# def new_overage():
#     """Enable overage for an account with no Stripe subscription"""
#     if current_user.allow_overage:
#         flash("Limit overage is already enabled")
#         return redirect(url_for("manage"))
#     if current_user.has_subscription:
#         if current_user.has_addon("overage"):
#             flash("Limit overage is already whitelisted for your account")
#             return redirect(url_for("manage"))
#         else:
#             return redirect(url_for("enable_overage"))
#     return render_template(
#         "first_addon.html",
#         stripe_key=app.config["STRIPE_PUB_KEY"],
#         session = plans.get_session(Addon.by_key("overage")),
#     )


@app.route("/plan/overage/enable")
@login_required
def enable_overage():
    """Enable overage for a subscribed account"""
    if current_user.allow_overage:
        flash("Limit overage is already enabled")
        return redirect(url_for("manage"))
    if not current_user.has_addon("overage"):
        if not current_user.has_subscription:
            # return redirect(url_for("new_overage"))
            flash("Limit overage currently requires a paid account")
            return redirect(url_for("manage"))
        current_user.add_addon("overage")
    current_user.allow_overage = True
    current_user.save()
    flash("Limit overage has been enabled")
    return redirect(url_for("manage"))


@app.route("/plan/overage/disable")
@login_required
def disable_overage():
    """Disable overage by flipping boolean"""
    if current_user.allow_overage:
        current_user.allow_overage = False
        current_user.save()
        flash("Limit overage has been disabled")
    else:
        flash("Limit overage is already disabled")
    return redirect(url_for("manage"))
