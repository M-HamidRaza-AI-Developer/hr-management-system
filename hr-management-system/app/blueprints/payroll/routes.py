from flask import render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user

from app.blueprints.payroll import bp
from app.extensions import db, redis_client
from app.decorators import roles_required, self_or_roles_required
from app.models.payroll import PayrollRecord, PayrollStatus
from app.models.employee import Employee
from app.models.user import Role
from app.utils.audit import log_action
from app.utils.tasks import generate_monthly_payroll
from rq import Queue


@bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.HR)
def list_payroll():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    query = PayrollRecord.query
    if year:
        query = query.filter_by(year=year)
    if month:
        query = query.filter_by(month=month)
    records = query.order_by(PayrollRecord.year.desc(), PayrollRecord.month.desc()).all()
    return render_template("payroll/list.html", records=records, year=year, month=month)


@bp.route("/generate", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def generate():
    """Kick off async generation of payroll for a given month via RQ worker."""
    year = request.form.get("year", type=int)
    month = request.form.get("month", type=int)

    try:
        queue = Queue("payroll", connection=redis_client)
        queue.enqueue(generate_monthly_payroll, year, month)
        flash(f"Payroll generation for {year}-{month:02d} has been queued.", "info")
    except Exception:
        # Fallback: run synchronously if no Redis/worker available (e.g. local dev)
        count = generate_monthly_payroll(year, month)
        flash(f"Generated {count} payroll record(s) for {year}-{month:02d}.", "success")

    log_action("payroll.generate", "PayrollRecord", None, {"year": year, "month": month})
    db.session.commit()
    return redirect(url_for("payroll.list_payroll", year=year, month=month))


@bp.route("/<int:record_id>/approve", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def approve(record_id):
    record = PayrollRecord.query.get_or_404(record_id)
    record.status = PayrollStatus.APPROVED
    log_action("payroll.approve", "PayrollRecord", record.id)
    db.session.commit()
    flash("Payroll record approved.", "success")
    return redirect(url_for("payroll.list_payroll"))


@bp.route("/<int:record_id>/payslip")
@login_required
@self_or_roles_required(
    lambda record_id: PayrollRecord.query.get_or_404(record_id).employee_id, Role.ADMIN, Role.HR
)
def download_payslip(record_id):
    record = PayrollRecord.query.get_or_404(record_id)
    if not record.payslip_pdf_path:
        abort(404, description="Payslip PDF has not been generated yet.")
    return send_file(record.payslip_pdf_path, as_attachment=True, download_name=f"payslip_{record.year}_{record.month:02d}.pdf")


@bp.route("/my-payslips")
@login_required
def my_payslips():
    if not current_user.employee:
        abort(400, description="No employee profile linked to this account.")
    records = (
        PayrollRecord.query.filter_by(employee_id=current_user.employee.id)
        .order_by(PayrollRecord.year.desc(), PayrollRecord.month.desc())
        .all()
    )
    return render_template("payroll/my_payslips.html", records=records)
