"""Role-based access control decorators."""
from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*roles):
    """Restrict a view to users whose role is in `roles`.

    Usage:
        @roles_required(Role.ADMIN, Role.HR)
        def some_view(): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role(*roles):
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def self_or_roles_required(get_employee_id, *roles):
    """Allow access if the current user IS the employee in question
    (via get_employee_id(**kwargs)) OR holds one of `roles`.

    Useful for endpoints like "view my own payslips" vs "HR viewing anyone's".
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            target_employee_id = get_employee_id(**kwargs)
            is_self = (
                current_user.employee is not None
                and current_user.employee.id == target_employee_id
            )
            if not (is_self or current_user.has_role(*roles)):
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
