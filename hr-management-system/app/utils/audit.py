"""Helper to write audit log entries consistently."""
from flask import request
from flask_login import current_user

from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(action: str, entity_type: str, entity_id: int | None = None, details: dict | None = None):
    """Record an audit log entry for the current request/user.

    Call this from routes/services right after a mutating action succeeds,
    e.g. log_action("leave.approve", "LeaveRequest", leave.id, {"days": leave.total_days}).
    """
    entry = AuditLog(
        user_id=current_user.id if getattr(current_user, "is_authenticated", False) else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(entry)
    # Intentionally not committing here — caller controls the transaction
    # boundary so the audit entry commits atomically with the real change.
