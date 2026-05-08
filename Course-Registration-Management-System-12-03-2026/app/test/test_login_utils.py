import hashlib
from unittest.mock import patch

import pytest

from app import utils
from app.model import User, UserRole
from app.test.test_base import test_app, test_client, test_session


EXPECTED_LOGIN_ERROR = "MSSV hoặc mật khẩu không chính xác"


def hashed_password(password):
    return hashlib.md5(password.strip().encode("utf-8")).hexdigest()


def seed_login_user(test_session):
    user = User(
        id=1,
        student_code="2354050999",
        password=hashed_password("123456"),
        role=UserRole.STUDENT,
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.mark.parametrize(
    ("student_code", "password"),
    [
        ("2354050999", "123456"),
        (" 2354050999 ", "123456"),
        ("2354050999", " 123456 "),
        (" 2354050999 ", " 123456 "),
    ],
)
def test_check_login_student_accepts_valid_credential_partitions(
    test_session, test_app, student_code, password
):
    with test_app.app_context():
        user = seed_login_user(test_session)

        result = utils.check_login_student(student_code, password)

        assert result is not None
        assert result.id == user.id
        assert result.student_code == "2354050999"


@pytest.mark.parametrize(
    ("student_code", "password"),
    [
        ("2354050000", "123456"),
        ("2354050999", "Mật khẩu sai nè"),
        ("2354050000", "Mật khẩu sai msssv cũng sai "),
    ],
)
def test_check_login_student_rejects_invalid_credential_partitions(
    test_session, test_app, student_code, password
):
    with test_app.app_context():
        seed_login_user(test_session)

        result = utils.check_login_student(student_code, password)

        assert result is None


@pytest.mark.parametrize(
    ("student_code", "password"),
    [
        ("", "123456"),
        ("2354050999", ""),
        ("", ""),
        (None, "123456"),
        ("2354050999", None),
        (" ", "123456"),
        ("2354050999", " "),
        (" ", " "),
    ],
)
def test_check_login_student_rejects_missing_credential_boundaries(
    test_session, test_app, student_code, password
):
    with test_app.app_context():
        seed_login_user(test_session)

        result = utils.check_login_student(student_code, password)

        assert result is None


def test_check_login_student_matches_exact_trimmed_student_code(test_session, test_app):
    with test_app.app_context():
        seed_login_user(test_session)
        test_session.add(
            User(
                id=2,
                student_code="2354050100",
                password=hashed_password("123456"),
                role=UserRole.STUDENT,
            )
        )
        test_session.commit()

        result = utils.check_login_student("2354050100", "123456")

        assert result is not None
        assert result.student_code == "2354050100"


def test_check_login_student_rejects_password_at_length_boundary(test_session, test_app):
    with test_app.app_context():
        seed_login_user(test_session)
        test_session.add(
            User(
                id=2,
                student_code="2354050100",
                password=hashed_password("1"),
                role=UserRole.STUDENT,
            )
        )
        test_session.commit()

        valid_result = utils.check_login_student("2354050100", "1")
        invalid_result = utils.check_login_student("2354050100", "")

        assert valid_result is not None
        assert valid_result.student_code == "2354050100"
        assert invalid_result is None


def test_check_login_student_rejects_student_code_at_length_boundary(
    test_session, test_app
):
    with test_app.app_context():
        test_session.add(
            User(
                id=1,
                student_code="1",
                password=hashed_password("123456"),
                role=UserRole.STUDENT,
            )
        )
        test_session.commit()

        valid_result = utils.check_login_student("1", "123456")
        invalid_result = utils.check_login_student("", "123456")

        assert valid_result is not None
        assert valid_result.student_code == "1"
        assert invalid_result is None


def test_login_route_returns_error_message_for_invalid_credentials(
    test_client
):
    from app import index as index_routes

    with patch.object(index_routes.utils, "check_login_student", return_value=None):
        with patch.object(
            index_routes, "render_template", return_value=EXPECTED_LOGIN_ERROR
        ) as render_template_mock:
            response = test_client.post(
                "/",
                data={"student_code": "2354050000", "password": "wrong-password"},
            )

    assert response.status_code == 200
    assert response.get_data(as_text=True) == EXPECTED_LOGIN_ERROR
    render_template_mock.assert_called_once_with(
        "login.html",
        err_msg=EXPECTED_LOGIN_ERROR,
    )


def test_login_student_redirects_to_index(test_client):
    from app import index as index_routes

    user = User(id=1, student_code="2354050999", role=UserRole.STUDENT)
    user.student = None

    with patch.object(index_routes.utils, "check_login_student", return_value=user):
        with patch.object(index_routes, "login_user"):
            with patch.object(index_routes, "url_for", return_value="/index"):
                response = test_client.post(
                    "/",
                    data={"login_role": "student", "student_code": "2354050999", "password": "123456"},
                )

    assert response.status_code == 302
    assert response.location.endswith("/index")


def test_login_admin_redirects_to_admin_course(test_client):
    from app import index as index_routes

    user = User(id=1, username="admin", role=UserRole.ADMIN)

    with patch.object(index_routes.utils, "check_login_admin", return_value=user):
        with patch.object(index_routes, "login_user"):
            with patch.object(index_routes, "url_for", return_value="/admin/course/"):
                response = test_client.post(
                    "/",
                    data={"login_role": "admin", "student_code": "admin", "password": "123456"},
                )

    assert response.status_code == 302
    assert "/admin/course/" in response.location


def test_logout_redirects_to_login(test_app, test_client):
    from app import index as index_routes

    test_app.add_url_rule("/logout", "logout", index_routes.logout)

    with patch.object(index_routes, "url_for", return_value="/"):
        response = test_client.get("/logout")

    assert response.status_code == 302
    assert response.location.endswith("/")
