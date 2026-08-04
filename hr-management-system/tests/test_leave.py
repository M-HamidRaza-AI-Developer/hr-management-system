from datetime import date, timedelta

from tests.conftest import login
from app.models.leave import LeaveType


def test_employee_can_apply_for_leave(client, employee_user, _db_session):
    leave_type = LeaveType(name="Annual Leave", default_days_per_year=20, is_paid=True)
    _db_session.add(leave_type)
    _db_session.commit()

    login(client, "employee@example.com", "password123")
    start = date.today() + timedelta(days=5)
    end = start + timedelta(days=2)
    response = client.post(
        "/leave/apply",
        data={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "reason": "Family trip",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"submitted" in response.data.lower()


def test_employee_cannot_access_pending_approvals(client, employee_user):
    login(client, "employee@example.com", "password123")
    response = client.get("/leave/pending")
    assert response.status_code == 403
