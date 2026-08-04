"""Leave management: leave types, requests, and per-employee balances."""
import enum
from datetime import date
from typing import Optional
from sqlalchemy import String, Date, ForeignKey, Enum, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveType(TimestampMixin, db.Model):
    """E.g. Annual, Sick, Unpaid, Maternity — configurable by HR/Admin."""

    __tablename__ = "leave_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    default_days_per_year: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_paid: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<LeaveType {self.name}>"


class LeaveRequest(TimestampMixin, db.Model):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    employee: Mapped["Employee"] = relationship(
        back_populates="leave_requests", foreign_keys=[employee_id]
    )

    leave_type_id: Mapped[int] = mapped_column(ForeignKey("leave_types.id"), nullable=False)
    leave_type: Mapped["LeaveType"] = relationship()

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False
    )

    reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id"), nullable=True
    )
    reviewed_by: Mapped[Optional["Employee"]] = relationship(foreign_keys=[reviewed_by_id])
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @property
    def total_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def __repr__(self) -> str:
        return f"<LeaveRequest emp={self.employee_id} {self.start_date}..{self.end_date} {self.status.value}>"


class LeaveBalance(TimestampMixin, db.Model):
    """Tracks remaining leave days per employee, per leave type, per year."""

    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id", "year", name="uq_leave_balance"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    employee: Mapped["Employee"] = relationship(back_populates="leave_balances")

    leave_type_id: Mapped[int] = mapped_column(ForeignKey("leave_types.id"), nullable=False)
    leave_type: Mapped["LeaveType"] = relationship()

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    allocated_days: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    used_days: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    @property
    def remaining_days(self) -> float:
        return float(self.allocated_days) - float(self.used_days)
