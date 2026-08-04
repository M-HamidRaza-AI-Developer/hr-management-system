"""PDF generation for payslips and reports, using reportlab."""
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_payslip_pdf(payroll_record, output_path: str) -> str:
    """Render a single payroll record as a PDF payslip and save to output_path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []

    employee = payroll_record.employee
    story.append(Paragraph("Payslip", styles["Title"]))
    story.append(Paragraph(f"{employee.full_name} ({employee.employee_code})", styles["Heading2"]))
    story.append(
        Paragraph(f"Period: {payroll_record.year}-{payroll_record.month:02d}", styles["Normal"])
    )
    story.append(Spacer(1, 10 * mm))

    data = [
        ["Item", "Amount"],
        ["Gross Salary", f"{payroll_record.gross_salary:.2f}"],
        ["Tax Deduction", f"-{payroll_record.tax_deduction:.2f}"],
        ["Other Deductions", f"-{payroll_record.other_deductions:.2f}"],
        ["Unpaid Leave Deduction", f"-{payroll_record.unpaid_leave_deduction:.2f}"],
        ["Net Salary", f"{payroll_record.net_salary:.2f}"],
    ]
    table = Table(data, colWidths=[100 * mm, 50 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return output_path


def generate_attendance_report_pdf(rows: list[dict], title: str, output_path: str) -> str:
    """Render a tabular attendance/leave report to PDF. `rows` is a list of
    dicts with consistent keys used as column headers."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = [Paragraph(title, styles["Title"]), Spacer(1, 6 * mm)]

    if rows:
        headers = list(rows[0].keys())
        data = [headers] + [[str(row.get(h, "")) for h in headers] for row in rows]
        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No data for the selected period.", styles["Normal"]))

    doc.build(story)
    return output_path
