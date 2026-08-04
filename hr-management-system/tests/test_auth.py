from tests.conftest import login


def test_login_success(client, admin_user):
    response = login(client, "admin@example.com", "password123")
    assert response.status_code == 200
    assert b"Dashboard" in response.data or b"Admin Dashboard" in response.data


def test_login_wrong_password(client, admin_user):
    response = login(client, "admin@example.com", "wrongpassword")
    assert b"Invalid username/email or password" in response.data


def test_logout(client, admin_user):
    login(client, "admin@example.com", "password123")
    response = client.get("/auth/logout", follow_redirects=True)
    assert b"logged out" in response.data.lower()


def test_login_required_redirects(client):
    response = client.get("/employees/", follow_redirects=True)
    assert b"log" in response.data.lower()  # redirected to login page


def test_landing_page_shown_when_logged_out(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign Up" in response.data
    assert b"Log In" in response.data


def test_default_admin_seeded_and_can_log_in(client):
    """The 'hamid' / 'hamid123' admin account is auto-created on startup."""
    response = login(client, "hamid", "hamid123")
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_signup_requires_terms_acceptance(client):
    response = client.post(
        "/auth/signup",
        data={
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123",
            # accept_terms intentionally omitted
        },
        follow_redirects=True,
    )
    assert b"Terms and Conditions" in response.data or b"must accept" in response.data.lower()


def test_signup_creates_account_and_logs_in(client):
    response = client.post(
        "/auth/signup",
        data={
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "accept_terms": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome" in response.data
