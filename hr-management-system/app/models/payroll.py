"""Payroll: recurring salary structure + generated monthly records."""
import enum
from typing import Optional
from sqlalchemy import ForeignKey, Enum, Numeric, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin


class PayrollStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PAID = "paid"


class SalaryStructure(TimestampMixin, db.Model):
    """The recurring, current compensation terms for an employee."""

    __tablename__ = "salary_structures"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"), unique=True, nullable=False
    )
    employee: Mapped["Employee"] = relationship(back_populates="salary_structure")

    base_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    housing_allowance: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    transport_allowance: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    other_allowance: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    tax_rate_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    @property
    def gross_salary(self) -> float:
        return float(
            self.base_salary
            + self.housing_allowance
            + self.transport_allowance
            + self.other_allowance
        )


class PayrollRecord(TimestampMixin, db.Model):
    """A generated, immutable-once-paid payslip for one employee/month."""

    __tablename__ = "payroll_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "year", "month", name="uq_payroll_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    employee: Mapped["Employee"] = relationship(back_populates="payroll_records")

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    gross_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax_deduction: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    other_deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    unpaid_leave_deduction: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    net_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    status: Mapped[PayrollStatus] = mapped_column(
        Enum(PayrollStatus), default=PayrollStatus.DRAFT, nullable=False
    )
    payslip_pdf_path: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<PayrollRecord emp={self.employee_id} {self.year}-{self.month:02d} {self.status.value}>"
