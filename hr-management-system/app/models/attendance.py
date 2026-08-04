"""Attendance model: one row per employee per day check-in/out."""
import enum
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"


class Attendance(TimestampMixin, db.Model):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    employee: Mapped["Employee"] = relationship(back_populates="attendance_records")

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(nullable=True)

    @property
    def hours_worked(self) -> Optional[float]:
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            return round(delta.total_seconds() / 3600, 2)
        return None

    def __repr__(self) -> str:
        return f"<Attendance emp={self.employee_id} {self.date} {self.status.value}>"
