from flask import Blueprint

bp = Blueprint("employees", __name__, url_prefix="/employees")

from app.blueprints.employees import routes  # noqa: E402,F401
