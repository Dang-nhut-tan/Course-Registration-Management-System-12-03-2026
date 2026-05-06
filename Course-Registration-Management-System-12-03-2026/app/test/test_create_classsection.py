from Demos.win32ts_logoff_disconnected import username

from app import db
import pytest
from unittest.mock import patch, MagicMock
from app.test.test_base import test_app, test_session
from app.admin import ClassSectionView
from app.model import ClassSection, User, UserRole

@pytest.fixture
def test_admin():
    return ClassSectionView(ClassSection, db.session)

@pytest.fixture
def mock_form():
    form = MagicMock()
    form.max_students.data = 50
    return form


def test_create_section_admin(test_app, test_admin, mock_form):
    admin_user = User(username= 'admin_user', role= UserRole.ADMIN)

    with test_app.test_request_context():
        with patch('app.admin.current_user', admin_user):
            with patch('flask_admin.contrib.sqla.ModelView.create_model', return_value=True):
                actual_result = test_admin.create_model(mock_form)

                assert actual_result is True

def test_create_section_others(test_app, test_admin, mock_form):
    student_user = User(username='student_user', role=UserRole.STUDENT)

    with test_app.test_request_context():
        with patch('app.admin.current_user', student_user):
            actual_result = test_admin.create_model(mock_form)

            assert actual_result is False