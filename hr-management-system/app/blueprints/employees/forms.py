from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional as OptionalValidator

from app.models.employee import EmploymentStatus
from app.models.user import Role


class EmployeeForm(FlaskForm):
    employee_code = StringField("Employee Code", validators=[DataRequired(), Length(max=20)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[OptionalValidator(), Length(max=30)])
    job_title = StringField("Job Title", validators=[DataRequired(), Length(max=120)])
    date_hired = DateField("Date Hired", validators=[DataRequired()])
    department_id = SelectField("Department", coerce=int, validators=[OptionalValidator()])
    manager_id = SelectField("Manager", coerce=int, validators=[OptionalValidator()])
    status = SelectField(
        "Status",
        choices=[(s.value, s.value.replace("_", " ").title()) for s in EmploymentStatus],
        validators=[DataRequired()],
    )
    role = SelectField(
        "System Role",
        choices=[(r.value, r.value.title()) for r in Role],
        validators=[DataRequired()],
    )
    # Only required when creating a new employee (new login account)
    initial_password = PasswordField("Initial Password", validators=[OptionalValidator(), Length(min=8)])
    submit = SubmitField("Save Employee")
