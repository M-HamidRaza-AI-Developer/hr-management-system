"""Import all models so Alembic autogenerate and SQLAlchemy metadata see them."""
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.leave import LeaveType, LeaveRequest, LeaveBalance
from app.models.payroll import PayrollRecord, SalaryStructure
from app.models.document import Document
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "Employee",
    "Department",
    "Attendance",
    "LeaveType",
    "LeaveRequest",
    "LeaveBalance",
    "PayrollRecord",
    "SalaryStructure",
    "Document",
    "AuditLog",
]
