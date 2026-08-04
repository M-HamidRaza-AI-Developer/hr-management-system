from datetime import date, datetime

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.blueprints.attendance import bp
from app.extensions import db
from app.decorators import roles_required
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.user import Role
from app.utils.audit import log_action


@bp.route("/check-in", methods=["POST"])
@login_required
def check_in():
    """Self-service check-in for the logged-in employee."""
    if not current_user.employee:
        abort(400, description="No employee profile linked to this account.")

    today = date.today()
    record = Attendance.query.filter_by(employee_id=current_user.employee.id, date=today).first()
    if record and record.check_in:
        flash("You've already checked in today.", "warning")
        return redirect(url_for("dashboard.index"))

    if not record:
        record = Attendance(employee_id=current_user.employee.id, date=today, status=AttendanceStatus.PRESENT)
        db.session.add(record)
    record.check_in = datetime.utcnow()
    db.session.commit()
    flash("Checked in successfully.", "success")
    return redirect(url_for("dashboard.index"))


@bp.route("/check-out", methods=["POST"])
@login_required
def check_out():
    if not current_user.employee:
        abort(400, description="No employee profile linked to this account.")

    today = date.today()
    record = Attendance.query.filter_by(employee_id=current_user.employee.id, date=today).first()
    if not record or not record.check_in:
        flash("You need to check in before checking out.", "warning")
        return redirect(url_for("dashboard.index"))

    record.check_out = datetime.utcnow()
    db.session.commit()
    flash("Checked out successfully.", "success")
    return redirect(url_for("dashboard.index"))


@bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.HR)
def list_attendance():
    page = request.args.get("page", 1, type=int)
    employee_id = request.args.get("employee_id", type=int)

    query = Attendance.query.order_by(Attendance.date.desc())
    if employee_id:
        query = query.filter_by(employee_id=employee_id)

    pagination = query.paginate(page=page, per_page=30, error_out=False)
    employees = Employee.query.order_by(Employee.first_name).all()
    return render_template(
        "attendance/list.html", pagination=pagination, employees=employees, employee_id=employee_id
    )


@bp.route("/mark", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def mark_attendance():
    """Manually mark/correct an employee's attendance for a given day (HR override)."""
    employee_id = request.form.get("employee_id", type=int)
    record_date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
    status = request.form.get("status")

    employee = Employee.query.get_or_404(employee_id)
    record = Attendance.query.filter_by(employee_id=employee.id, date=record_date).first()
    if not record:
        record = Attendance(employee_id=employee.id, date=record_date)
        db.session.add(record)
    record.status = AttendanceStatus(status)

    log_action("attendance.mark", "Attendance", record.id, {"status": status, "date": str(record_date)})
    db.session.commit()
    flash("Attendance updated.", "success")
    return redirect(url_for("attendance.list_attendance"))
