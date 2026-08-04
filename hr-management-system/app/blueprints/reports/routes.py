import os
import uuid
from datetime import datetime

from flask import render_template, request, send_file, current_app
from flask_login import login_required

from app.blueprints.reports import bp
from app.decorators import roles_required
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest
from app.models.employee import Employee
from app.models.user import Role
from app.utils.pdf import generate_attendance_report_pdf


@bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.HR)
def index():
    return render_template("reports/index.html")


@bp.route("/attendance", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def attendance_report():
    if request.method == "POST":
        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()

        records = (
            Attendance.query.filter(Attendance.date.between(start_date, end_date))
            .order_by(Attendance.date)
            .all()
        )
        rows = [
            {
                "Employee": r.employee.full_name,
                "Date": r.date.isoformat(),
                "Status": r.status.value,
                "Check In": r.check_in.strftime("%H:%M") if r.check_in else "-",
                "Check Out": r.check_out.strftime("%H:%M") if r.check_out else "-",
                "Hours": r.hours_worked or "-",
            }
            for r in records
        ]

        output_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "reports", f"attendance_{uuid.uuid4().hex}.pdf"
        )
        generate_attendance_report_pdf(
            rows, f"Attendance Report: {start_date} to {end_date}", output_path
        )
        return send_file(output_path, as_attachment=True, download_name="attendance_report.pdf")

    return render_template("reports/attendance_form.html")


@bp.route("/leave-summary", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def leave_summary_report():
    if request.method == "POST":
        year = int(request.form["year"])
        requests_ = LeaveRequest.query.filter(
            LeaveRequest.start_date >= f"{year}-01-01",
            LeaveRequest.start_date <= f"{year}-12-31",
        ).all()
        rows = [
            {
                "Employee": r.employee.full_name,
                "Leave Type": r.leave_type.name,
                "Start": r.start_date.isoformat(),
                "End": r.end_date.isoformat(),
                "Days": r.total_days,
                "Status": r.status.value,
            }
            for r in requests_
        ]
        output_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "reports", f"leave_{uuid.uuid4().hex}.pdf"
        )
        generate_attendance_report_pdf(rows, f"Leave Summary: {year}", output_path)
        return send_file(output_path, as_attachment=True, download_name="leave_summary.pdf")

    return render_template("reports/leave_form.html")
