from datetime import date

from flask import render_template
from flask_login import login_required, current_user

from app.blueprints.dashboard import bp
from app.models.employee import Employee, EmploymentStatus
from app.models.department import Department
from app.models.leave import LeaveRequest, LeaveStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import Role


@bp.route("/")
@login_required
def index():
    context = {"today": date.today()}

    if current_user.has_role(Role.ADMIN, Role.HR):
        total_employees = Employee.query.filter_by(status=EmploymentStatus.ACTIVE).count()
        today_present_count = Attendance.query.filter_by(
            date=date.today(), status=AttendanceStatus.PRESENT
        ).count()

        context["total_employees"] = total_employees
        context["total_departments"] = Department.query.count()
        context["pending_leave_count"] = LeaveRequest.query.filter_by(status=LeaveStatus.PENDING).count()
        context["today_present_count"] = today_present_count

        # Attendance donut: percentage of active employees marked present today.
        context["present_percent"] = (
            round((today_present_count / total_employees) * 100) if total_employees else 0
        )

        context["recent_company_leave_requests"] = (
            LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).limit(5).all()
        )
        return render_template("dashboard/admin.html", **context)

    # Employee self-service dashboard
    employee = current_user.employee
    context["employee"] = employee
    if employee:
        context["today_attendance"] = Attendance.query.filter_by(
            employee_id=employee.id, date=date.today()
        ).first()
        context["recent_leave_requests"] = (
            LeaveRequest.query.filter_by(employee_id=employee.id)
            .order_by(LeaveRequest.created_at.desc())
            .limit(5)
            .all()
        )
        context["pending_leave_count"] = LeaveRequest.query.filter_by(
            employee_id=employee.id, status=LeaveStatus.PENDING
        ).count()
        context["approved_leave_count"] = LeaveRequest.query.filter_by(
            employee_id=employee.id, status=LeaveStatus.APPROVED
        ).count()
    return render_template("dashboard/employee.html", **context)
