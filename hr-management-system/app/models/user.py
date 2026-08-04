"""User model: authentication + role-based access control."""
import enum
from typing import Optional
from flask_login import UserMixin
from sqlalchemy import String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.mixins import TimestampMixin


class Role(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    EMPLOYEE = "employee"


class User(UserMixin, TimestampMixin, db.Model):
    """Login identity. Kept separate from Employee so not every login
    needs an employee profile (e.g. a pure system admin)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.EMPLOYEE, nullable=False)
    is_active_user: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    employee: Mapped[Optional["Employee"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Flask-Login expects `is_active`; property avoids clashing with the
    # is_active_user column name while keeping DB column explicit.
    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return self.is_active_user

    def has_role(self, *roles: Role) -> bool:
        return self.role in roles

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
