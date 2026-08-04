from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.blueprints.departments import bp
from app.extensions import db
from app.decorators import roles_required
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import Role
from app.utils.audit import log_action


@bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.HR)
def list_departments():
    departments = Department.query.order_by(Department.name).all()
    return render_template("departments/list.html", departments=departments)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def create_department():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        manager_id = request.form.get("manager_id", type=int) or None
        if not name:
            flash("Department name is required.", "danger")
        elif Department.query.filter_by(name=name).first():
            flash("A department with that name already exists.", "danger")
        else:
            dept = Department(name=name, description=description or None, manager_id=manager_id)
            db.session.add(dept)
            db.session.flush()
            log_action("department.create", "Department", dept.id, {"name": name})
            db.session.commit()
            flash(f"Department '{name}' created.", "success")
            return redirect(url_for("departments.list_departments"))

    employees = Employee.query.order_by(Employee.first_name).all()
    return render_template("departments/form.html", department=None, employees=employees)


@bp.route("/<int:department_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    if request.method == "POST":
        department.name = request.form.get("name", "").strip()
        department.description = request.form.get("description", "").strip() or None
        department.manager_id = request.form.get("manager_id", type=int) or None
        log_action("department.update", "Department", department.id)
        db.session.commit()
        flash(f"Department '{department.name}' updated.", "success")
        return redirect(url_for("departments.list_departments"))

    employees = Employee.query.order_by(Employee.first_name).all()
    return render_template("departments/form.html", department=department, employees=employees)


@bp.route("/<int:department_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    if department.employees:
        flash("Cannot delete a department that still has employees assigned.", "danger")
        return redirect(url_for("departments.list_departments"))
    name = department.name
    log_action("department.delete", "Department", department.id, {"name": name})
    db.session.delete(department)
    db.session.commit()
    flash(f"Department '{name}' deleted.", "info")
    return redirect(url_for("departments.list_departments"))
