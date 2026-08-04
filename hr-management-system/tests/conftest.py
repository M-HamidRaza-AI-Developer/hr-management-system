import os
import tempfile
import pytest
from datetime import date

from app import create_app
from app.extensions import db as _db
from app.models.user import User, Role
from app.models.employee import Employee, EmploymentStatus


@pytest.fixture
def app():
    """Fresh app + fresh in-memory database per test. Simpler and more
    robust across SQLAlchemy versions than a shared-session/rollback
    pattern, at the cost of recreating tables each test (fine at this scale)."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    # Override the DB URI via config_overrides (rather than env var) since
    # Config classes read os.environ at import time, which is too early for
    # a per-test temp file, and the engine is built during create_app().
    app = create_app("testing", config_overrides={"SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def _db_session(app):
    with app.app_context():
        yield _db.session


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(_db_session):
    user = User(email="admin@example.com", role=Role.ADMIN)
    user.set_password("password123")
    _db_session.add(user)
    _db_session.flush()
    employee = Employee(
        employee_code="TEST0001",
        first_name="Ada",
        last_name="Admin",
        job_title="Administrator",
        date_hired=date(2024, 1, 1),
        status=EmploymentStatus.ACTIVE,
        user_id=user.id,
    )
    _db_session.add(employee)
    _db_session.commit()
    return user


@pytest.fixture
def employee_user(_db_session):
    user = User(email="employee@example.com", role=Role.EMPLOYEE)
    user.set_password("password123")
    _db_session.add(user)
    _db_session.flush()
    employee = Employee(
        employee_code="TEST0002",
        first_name="Eve",
        last_name="Employee",
        job_title="Engineer",
        date_hired=date(2024, 1, 1),
        status=EmploymentStatus.ACTIVE,
        user_id=user.id,
    )
    _db_session.add(employee)
    _db_session.commit()
    return user


def login(client, email, password):
    return client.post(
        "/auth/login",
        data={"identifier": email, "password": password},
        follow_redirects=True,
    )
