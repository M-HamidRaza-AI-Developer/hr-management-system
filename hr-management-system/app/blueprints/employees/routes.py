from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.blueprints.employees import bp
from app.blueprints.employees.forms import EmployeeForm
from app.extensions import db
from app.decorators import roles_required, self_or_roles_required
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User, Role
from app.utils.audit import log_action


def _populate_choices(form: EmployeeForm, exclude_employee_id: int | None = None):
    departments = Department.query.order_by(Department.name).all()
    form.department_id.choices = [(0, "-- None --")] + [(d.id, d.name) for d in departments]

    managers_query = Employee.query.order_by(Employee.first_name)
    if exclude_employee_id:
        managers_query = managers_query.filter(Employee.id != exclude_employee_id)
    form.manager_id.choices = [(0, "-- None --")] + [
        (e.id, e.full_name) for e in managers_query.all()
    ]


@bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.HR)
def list_employees():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "", type=str).strip()

    query = Employee.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.employee_code.ilike(like),
                Employee.job_title.ilike(like),
            )
        )

    pagination = query.order_by(Employee.last_name).paginate(page=page, per_page=20, error_out=False)
    return render_template("employees/list.html", pagination=pagination, search=search)


@bp.route("/<int:employee_id>")
@login_required
@self_or_roles_required(lambda employee_id: employee_id, Role.ADMIN, Role.HR)
def view_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    return render_template("employees/detail.html", employee=employee)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def create_employee():
    form = EmployeeForm()
    _populate_choices(form)

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("A user with that email already exists.", "danger")
            return render_template("employees/form.html", form=form, employee=None)
        if not form.initial_password.data:
            flash("An initial password is required for a new employee.", "danger")
            return render_template("employees/form.html", form=form, employee=None)

        user = User(email=form.email.data.lower().strip(), role=Role(form.role.data), must_change_password=True)
        user.set_password(form.initial_password.data)
        db.session.add(user)
        db.session.flush()  # get user.id without committing

        employee = Employee(
            employee_code=form.employee_code.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data or None,
            job_title=form.job_title.data,
            date_hired=form.date_hired.data,
            department_id=form.department_id.data or None,
            manager_id=form.manager_id.data or None,
            status=form.status.data,
            user_id=user.id,
        )
        db.session.add(employee)
        db.session.flush()
        log_action("employee.create", "Employee", employee.id, {"employee_code": employee.employee_code})
        db.session.commit()

        flash(f"Employee {employee.full_name} created.", "success")
        return redirect(url_for("employees.view_employee", employee_id=employee.id))

    return render_template("employees/form.html", form=form, employee=None)


@bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)
    _populate_choices(form, exclude_employee_id=employee.id)

    if request.method == "GET":
        form.email.data = employee.user.email
        form.role.data = employee.user.role.value
        form.department_id.data = employee.department_id or 0
        form.manager_id.data = employee.manager_id or 0

    if form.validate_on_submit():
        employee.employee_code = form.employee_code.data
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.phone = form.phone.data or None
        employee.job_title = form.job_title.data
        employee.date_hired = form.date_hired.data
        employee.department_id = form.department_id.data or None
        employee.manager_id = form.manager_id.data or None
        employee.status = form.status.data
        employee.user.role = Role(form.role.data)
        if form.initial_password.data:
            employee.user.set_password(form.initial_password.data)

        log_action("employee.update", "Employee", employee.id)
        db.session.commit()
        flash(f"Employee {employee.full_name} updated.", "success")
        return redirect(url_for("employees.view_employee", employee_id=employee.id))

    return render_template("employees/form.html", form=form, employee=employee)


@bp.route("/<int:employee_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    name = employee.full_name
    log_action("employee.delete", "Employee", employee.id, {"name": name})
    db.session.delete(employee)  # cascades to user via relationship
    db.session.commit()
    flash(f"Employee {name} removed.", "info")
    return redirect(url_for("employees.list_employees"))
