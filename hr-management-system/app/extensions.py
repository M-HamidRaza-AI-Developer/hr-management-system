"""Central location for Flask extension instances, initialized without an app.

Keeping extensions here (instead of inside __init__.py) avoids circular
imports: models and blueprints can import `db`, `login_manager`, etc.
directly without importing the application factory itself.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
import redis as redis_lib

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

redis_client = None


def init_redis(app):
    global redis_client
    redis_client = redis_lib.from_url(app.config["REDIS_URL"])
    return redis_client
