from datetime import date

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import bp
from app.blueprints.auth.forms import LoginForm, SignupForm, ChangePasswordForm
from app.extensions import db
from app.models.user import User, Role
from app.models.employee import Employee, EmploymentStatus
from app.utils.audit import log_action


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip().lower()
        user = User.query.filter(db.func.lower(User.email) == identifier).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username/email or password.", "danger")
            return redirect(url_for("auth.login"))
        if not user.is_active_user:
            flash("This account has been deactivated. Contact an administrator.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember_me.data)
        log_action("auth.login", "User", user.id)
        db.session.commit()

        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("dashboard.index")
        return redirect(next_page)

    return render_template("auth/login.html", form=form)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter(db.func.lower(User.email) == email).first():
            flash("An account with that email already exists. Please log in instead.", "danger")
            return redirect(url_for("auth.login"))

        user = User(email=email, role=Role.EMPLOYEE)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        employee_count = Employee.query.count()
        employee = Employee(
            employee_code=f"EMP{employee_count + 1:04d}",
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            job_title="Not Assigned",
            date_hired=date.today(),
            status=EmploymentStatus.ACTIVE,
            user_id=user.id,
        )
        db.session.add(employee)
        db.session.flush()

        log_action("auth.signup", "User", user.id, {"email": email})
        db.session.commit()

        login_user(user)
        flash(f"Welcome, {employee.first_name}! Your account has been created.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/signup.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    log_action("auth.logout", "User", current_user.id)
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("auth.change_password"))
        current_user.set_password(form.new_password.data)
        current_user.must_change_password = False
        log_action("auth.change_password", "User", current_user.id)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("auth/change_password.html", form=form)
