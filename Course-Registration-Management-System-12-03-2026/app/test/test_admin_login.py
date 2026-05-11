from unittest.mock import patch
from app.test.test_base import test_app, test_session
from app.admin import IndexView
from app.model import User, UserRole

def test_admin_access_required(test_app, test_session):
    view = IndexView()
    with test_app.test_request_context():
        with patch('flask_login.utils._get_user') as mocked_user:
            mocked_user.return_value = User(role=UserRole.ADMIN)
            assert view.is_accessible() is True