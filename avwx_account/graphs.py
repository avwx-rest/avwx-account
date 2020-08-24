"""
Application graph views
"""

# pylint: disable=missing-function-docstring,protected-access

# stdlib
import json
from typing import List

# library
from flask import redirect, render_template, request, url_for
from flask_user import login_required, current_user

# module
from avwx_account import app

COLORS = ("red", "orange", "yellow", "green", "blue", "purple", "pink")


def format_count(
    label: str, counts: List[int], color: str, dashed: bool = False
) -> dict:
    """
    Format a line dataset for chart.js
    """
    ret = {
        "label": label,
        "data": counts,
        "borderColor": color,
        "borderWidth": 2,
        "fill": False,
    }
    if dashed:
        ret["borderDash"] = [5, 5]
    return ret


@app.route("/token/usage")
@login_required
def token_usage():
    token_type = request.args.get("type", "app")
    target = request.args.get("value")
    if target:
        try:
            target = current_user.get_token(target)._id
        except:
            pass
    counts = current_user.token_usage()
    if not counts:
        return redirect(url_for("manage"))
    labels = json.dumps([d.strftime("%b %d") for d in counts["days"]])
    data = []
    if token_type != "dev":
        data.append(format_count("Total", counts["total"], "black", dashed=True))
    for i, item in enumerate(counts[token_type].items()):
        token_id, counts = item
        token = current_user.get_token(_id=token_id)
        if target and token._id != target:
            continue
        color = COLORS[i % len(COLORS)]
        data.append(format_count(token.name, counts, color))
    data = json.dumps(data)
    return render_template("token_usage.html", labels=labels, data=data)
