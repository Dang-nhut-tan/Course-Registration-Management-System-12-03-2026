from unittest.mock import patch

import pytest

from app import db
from app.api import EnrollmentRegistrationResult, api
from app.model import Faculty, User, UserRole
from app.test.test_base import test_app


@pytest.fixture
def api_client(test_app):
    test_app.register_blueprint(api)
    return test_app.test_client()


def _login(client, user_id):
    with client.session_transaction() as login_session:
        login_session["_user_id"] = str(user_id)
        login_session["_fresh"] = True


def test_admin_api_rejects_anonymous_user(api_client):
    response = api_client.get("/api/admin/courses")
    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_admin_api_crud_course(test_app, api_client):
    with test_app.app_context():
        db.session.add_all([
            User(id=1, username="api-admin", password="hash", role=UserRole.ADMIN),
            Faculty(id=1, name="CNTT"),
        ])
        db.session.commit()

    _login(api_client, 1)
    created = api_client.post("/api/admin/courses", json={
        "name": "Lập trình API", "credits": 3,
        "is_shared": False, "faculty_id": 1,
    })
    assert created.status_code == 201
    course_id = created.get_json()["data"]["id"]

    updated = api_client.patch(
        f"/api/admin/courses/{course_id}", json={"credits": 4}
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["credits"] == 4

    deleted = api_client.delete(f"/api/admin/courses/{course_id}")
    assert deleted.status_code == 204


def test_student_enrollment_api_uses_logged_in_student(api_client):
    with api_client.session_transaction() as student_session:
        student_session["student_code"] = "SV001"

    with patch(
        "app.api.register_enrollment",
        return_value=EnrollmentRegistrationResult(),
    ) as register:
        response = api_client.post("/api/enrollments", json={"class_section_id": 12})

    assert response.status_code == 201
    register.assert_called_once_with("SV001", 12)
