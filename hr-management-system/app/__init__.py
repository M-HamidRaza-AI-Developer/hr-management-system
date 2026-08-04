"""Application factory."""
import os
from flask import Flask, render_template

from app.config import config
from app.extensions import db, login_manager, mail, csrf, init_redis


def create_app(config_name: str | None = None, config_overrides: dict | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    if config_overrides:
        app.config.update(config_overrides)

    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_cli(app)
    _init_database(app)

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    init_redis(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.main import bp as main_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.dashboard import bp as dashboard_bp
    from app.blueprints.employees import bp as employees_bp
    from app.blueprints.departments import bp as departments_bp
    from app.blueprints.attendance import bp as attendance_bp
    from app.blueprints.leave import bp as leave_bp
    from app.blueprints.payroll import bp as payroll_bp
    from app.blueprints.documents import bp as documents_bp
    from app.blueprints.reports import bp as reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(reports_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_cli(app: Flask) -> None:
    from app.cli import register_cli_commands

    register_cli_commands(app)


def _init_database(app: Flask) -> None:
    """Create all tables directly from the SQLAlchemy models (no Alembic/
    migrations) and make sure the built-in admin account exists.

    This runs once per app startup. It's intentionally simple: `create_all`
    only ever adds tables/columns that don't exist yet, it never alters or
    drops existing ones, so it's safe to run every time the app boots.
    """
    with app.app_context():
        db.create_all()
        _ensure_default_admin()


def _ensure_default_admin() -> None:
    from datetime import date
    from app.models.user import User, Role
    from app.models.employee import Employee, EmploymentStatus

    existing = User.query.filter_by(email="hamid").first()
    if existing:
        return

    admin_user = User(email="hamid", role=Role.ADMIN, must_change_password=False)
    admin_user.set_password("hamid123")
    db.session.add(admin_user)
    db.session.flush()

    admin_employee = Employee(
        employee_code="EMP0001",
        first_name="Hamid",
        last_name="Admin",
        job_title="System Administrator",
        date_hired=date.today(),
        status=EmploymentStatus.ACTIVE,
        user_id=admin_user.id,
    )
    db.session.add(admin_employee)
    db.session.commit()
