from flask import render_template, redirect, url_for
from flask_login import current_user

from app.blueprints.main import bp


@bp.route("/")
def index():
    """Public landing page. Logged-in users skip straight to their dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("main/landing.html")
