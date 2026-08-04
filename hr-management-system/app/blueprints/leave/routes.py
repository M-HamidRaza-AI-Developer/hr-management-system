from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.blueprints.leave import bp
from app.extensions import db
from app.decorators import roles_required
from app.models.leave import LeaveRequest, LeaveType, LeaveStatus, LeaveBalance
from app.models.user import Role
from app.utils.audit import log_action
from app.utils.email import notify_leave_request_submitted, notify_leave_request_reviewed


@bp.route("/")
@login_required
def my_leave_requests():
    if not current_user.employee:
        abort(400, description="No employee profile linked to this account.")
    requests_ = (
        LeaveRequest.query.filter_by(employee_id=current_user.employee.id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )
    leave_types = LeaveType.query.order_by(LeaveType.name).all()
    balances = LeaveBalance.query.filter_by(employee_id=current_user.employee.id).all()
    return render_template(
        "leave/list.html", requests=requests_, leave_types=leave_types, balances=balances
    )


@bp.route("/apply", methods=["POST"])
@login_required
def apply():
    if not current_user.employee:
        abort(400, description="No employee profile linked to this account.")

    leave_type_id = request.form.get("leave_type_id", type=int)
    start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
    end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()
    reason = request.form.get("reason", "").strip()

    if end_date < start_date:
        flash("End date cannot be before start date.", "danger")
        return redirect(url_for("leave.my_leave_requests"))

    leave_request = LeaveRequest(
        employee_id=current_user.employee.id,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason or None,
        status=LeaveStatus.PENDING,
    )
    db.session.add(leave_request)
    db.session.flush()
    log_action("leave.apply", "LeaveRequest", leave_request.id)
    db.session.commit()

    notify_leave_request_submitted(leave_request)
    flash("Leave request submitted.", "success")
    return redirect(url_for("leave.my_leave_requests"))


@bp.route("/pending")
@login_required
@roles_required(Role.ADMIN, Role.HR)
def pending_approvals():
    """HR/Admin queue of all pending leave requests. A team-manager view could
    additionally filter by `LeaveRequest.employee.manager_id == current_user.employee.id`."""
    page = request.args.get("page", 1, type=int)
    pagination = (
        LeaveRequest.query.filter_by(status=LeaveStatus.PENDING)
        .order_by(LeaveRequest.created_at)
        .paginate(page=page, per_page=20, error_out=False)
    )
    return render_template("leave/pending.html", pagination=pagination)


@bp.route("/<int:request_id>/review", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def review(request_id):
    leave_request = LeaveRequest.query.get_or_404(request_id)
    decision = request.form.get("decision")  # "approved" or "rejected"
    notes = request.form.get("notes", "").strip()

    if decision not in ("approved", "rejected"):
        abort(400)

    leave_request.status = LeaveStatus(decision)
    leave_request.reviewed_by_id = current_user.employee.id if current_user.employee else None
    leave_request.review_notes = notes or None

    if decision == "approved":
        balance = LeaveBalance.query.filter_by(
            employee_id=leave_request.employee_id,
            leave_type_id=leave_request.leave_type_id,
            year=leave_request.start_date.year,
        ).first()
        if balance:
            balance.used_days = float(balance.used_days) + leave_request.total_days

    log_action("leave.review", "LeaveRequest", leave_request.id, {"decision": decision})
    db.session.commit()

    notify_leave_request_reviewed(leave_request)
    flash(f"Leave request {decision}.", "success")
    return redirect(url_for("leave.pending_approvals"))
