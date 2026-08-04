"""Department model."""
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Self-referential: a department can report up to a parent department.
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    parent: Mapped[Optional["Department"]] = relationship(
        remote_side="Department.id", back_populates="children"
    )
    children: Mapped[List["Department"]] = relationship(back_populates="parent")

    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", use_alter=True, name="fk_department_manager"), nullable=True
    )
    manager: Mapped[Optional["Employee"]] = relationship(
        foreign_keys=[manager_id], post_update=True
    )

    employees: Mapped[List["Employee"]] = relationship(
        back_populates="department", foreign_keys="Employee.department_id"
    )

    def __repr__(self) -> str:
        return f"<Department {self.name}>"
