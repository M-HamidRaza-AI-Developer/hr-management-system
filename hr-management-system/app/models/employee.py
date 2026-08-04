"""Employee model — the central profile record."""
import enum
from datetime import date
from typing import Optional, List
from sqlalchemy import String, Date, ForeignKey, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class Employee(TimestampMixin, db.Model):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_hired: Mapped[date] = mapped_column(Date, nullable=False)
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[EmploymentStatus] = mapped_column(
        Enum(EmploymentStatus), default=EmploymentStatus.ACTIVE, nullable=False
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    user: Mapped["User"] = relationship(back_populates="employee")

    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    department: Mapped[Optional["Department"]] = relationship(
        back_populates="employees", foreign_keys=[department_id]
    )

    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"), nullable=True)
    manager: Mapped[Optional["Employee"]] = relationship(
        remote_side="Employee.id", back_populates="direct_reports"
    )
    direct_reports: Mapped[List["Employee"]] = relationship(back_populates="manager")

    attendance_records: Mapped[List["Attendance"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    leave_requests: Mapped[List["LeaveRequest"]] = relationship(
        back_populates="employee",
        foreign_keys="LeaveRequest.employee_id",
        cascade="all, delete-orphan",
    )
    leave_balances: Mapped[List["LeaveBalance"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    payroll_records: Mapped[List["PayrollRecord"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    salary_structure: Mapped[Optional["SalaryStructure"]] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Employee {self.employee_code} {self.full_name}>"
