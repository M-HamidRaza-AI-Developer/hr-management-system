"""Background jobs executed by the RQ worker (see worker.py)."""
from datetime import date

from app.extensions import db
from app.models.payroll import PayrollRecord, PayrollStatus
from app.models.employee import Employee, EmploymentStatus
from app.utils.pdf import generate_payslip_pdf


def generate_monthly_payroll(year: int, month: int):
    """Create draft PayrollRecords for every active employee for a given period.

    Enqueued from the payroll blueprint so the (potentially slow) generation
    of many records + PDFs doesn't block the web request.
    """
    employees = Employee.query.filter_by(status=EmploymentStatus.ACTIVE).all()
    created = []
    for employee in employees:
        existing = PayrollRecord.query.filter_by(
            employee_id=employee.id, year=year, month=month
        ).first()
        if existing:
            continue
        structure = employee.salary_structure
        if not structure:
            continue

        gross = structure.gross_salary
        tax = gross * float(structure.tax_rate_percent) / 100
        net = gross - tax

        record = PayrollRecord(
            employee_id=employee.id,
            year=year,
            month=month,
            gross_salary=gross,
            tax_deduction=tax,
            other_deductions=0,
            unpaid_leave_deduction=0,
            net_salary=net,
            status=PayrollStatus.DRAFT,
        )
        db.session.add(record)
        created.append(record)

    db.session.commit()

    for record in created:
        path = f"app/static/uploads/payslips/{record.employee_id}_{year}_{month:02d}.pdf"
        generate_payslip_pdf(record, path)
        record.payslip_pdf_path = path
    db.session.commit()

    return len(created)
