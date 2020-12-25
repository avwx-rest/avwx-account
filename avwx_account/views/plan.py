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


@app.route("/plan/overage")
@login_required
def toggle_overage():
    if current_user.plan.overage:
        current_user.allow_overage = not current_user.allow_overage
        state = "en" if current_user.allow_overage else "dis"
        flash(f"Limit overage has been {state}abled")
    else:
        current_user.allow_overage = False
    current_user.save()
    return redirect(url_for("manage"))
