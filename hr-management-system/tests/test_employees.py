from tests.conftest import login


def test_admin_can_list_employees(client, admin_user):
    login(client, "admin@example.com", "password123")
    response = client.get("/employees/")
    assert response.status_code == 200
    assert b"Employees" in response.data


def test_employee_cannot_list_all_employees(client, employee_user):
    login(client, "employee@example.com", "password123")
    response = client.get("/employees/")
    assert response.status_code == 403


def test_employee_can_view_own_profile(client, employee_user):
    login(client, "employee@example.com", "password123")
    response = client.get(f"/employees/{employee_user.employee.id}")
    assert response.status_code == 200


def test_admin_can_create_employee(client, admin_user):
    login(client, "admin@example.com", "password123")
    response = client.post(
        "/employees/new",
        data={
            "employee_code": "EMP0099",
            "first_name": "New",
            "last_name": "Hire",
            "email": "newhire@example.com",
            "job_title": "Analyst",
            "date_hired": "2026-01-15",
            "department_id": 0,
            "manager_id": 0,
            "status": "active",
            "role": "employee",
            "initial_password": "temporarypass1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"created" in response.data.lower()
