"""Email notification helpers, dispatched as background jobs via RQ."""
from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail, redis_client
from rq import Queue


def get_queue() -> Queue:
    return Queue("emails", connection=redis_client)


def _send_email_now(subject: str, recipients: list[str], template: str, **context):
    """Actual send — runs inside the RQ worker process, not the web request."""
    msg = Message(subject=subject, recipients=recipients)
    msg.html = render_template(template, **context)
    mail.send(msg)


def send_email_async(subject: str, recipients: list[str], template: str, **context):
    """Enqueue an email to be sent by the background worker.

    Falls back to a synchronous send if Redis/RQ isn't reachable (e.g. in
    tests or a minimal dev setup without the worker running).
    """
    try:
        queue = get_queue()
        queue.enqueue(_send_email_now, subject, recipients, template, **context)
    except Exception:  # noqa: BLE001 - broad on purpose, this is a best-effort fallback
        current_app.logger.warning("RQ unavailable, sending email synchronously", exc_info=True)
        with current_app.app_context():
            _send_email_now(subject, recipients, template, **context)


def notify_leave_request_submitted(leave_request):
    manager = leave_request.employee.manager
    if manager and manager.user:
        send_email_async(
            subject="New leave request pending your approval",
            recipients=[manager.user.email],
            template="emails/leave_submitted.html",
            leave_request=leave_request,
        )


def notify_leave_request_reviewed(leave_request):
    send_email_async(
        subject=f"Your leave request has been {leave_request.status.value}",
        recipients=[leave_request.employee.user.email],
        template="emails/leave_reviewed.html",
        leave_request=leave_request,
    )
