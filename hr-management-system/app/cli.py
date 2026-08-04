"""Custom Flask CLI commands: `flask seed-db`, `flask create-admin`."""
import click
from datetime import date

from app.extensions import db
from app.models.user import User, Role
from app.models.employee import Employee, EmploymentStatus
from app.models.department import Department
from app.models.leave import LeaveType


def register_cli_commands(app):
    @app.cli.command("create-admin")
    @click.argument("email")
    @click.argument("password")
    def create_admin(email, password):
        """Create an initial admin user + employee profile."""
        if User.query.filter_by(email=email).first():
            click.echo("A user with that email already exists.")
            return

        user = User(email=email.lower().strip(), role=Role.ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        employee = Employee(
            employee_code="EMP0001",
            first_name="System",
            last_name="Admin",
            job_title="Administrator",
            date_hired=date.today(),
            status=EmploymentStatus.ACTIVE,
            user_id=user.id,
        )
        db.session.add(employee)
        db.session.commit()
        click.echo(f"Admin user created: {email}")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed baseline reference data (leave types, a default department)."""
        defaults = [
            ("Annual Leave", 20, True),
            ("Sick Leave", 10, True),
            ("Unpaid Leave", 0, False),
            ("Maternity/Paternity Leave", 90, True),
        ]
        for name, days, paid in defaults:
            if not LeaveType.query.filter_by(name=name).first():
                db.session.add(LeaveType(name=name, default_days_per_year=days, is_paid=paid))

        if not Department.query.filter_by(name="General").first():
            db.session.add(Department(name="General", description="Default department"))

        db.session.commit()
        click.echo("Database seeded with default leave types and department.")
