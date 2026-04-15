from app import db
import pytest
from app.model import ClassSection, Enrollment
from app.admin import ClassSectionView
from app.test.test_base import test_app, test_session


@pytest.fixture
def test_admin():
    return ClassSectionView(ClassSection, db.session)

@pytest.fixture
def sample_class_section(test_session):
    cs1 = ClassSection(id= 1, semester="2024-1", max_students=50)

    test_session.add(cs1)
    test_session.commit()

    return cs1

@pytest.fixture
def sample_enrollment(sample_class_section, test_session):
    e1 = Enrollment(student_code= "2354050111", class_section_id= sample_class_section.id, status= "registered")

    test_session.add(e1)
    test_session.commit()

    return e1

def test_delete_class_section(test_admin, sample_class_section, sample_enrollment, test_session, test_app):
    with test_app.test_request_context():
        actual_class_section = test_admin.delete_model(sample_class_section)
        assert actual_class_section is False

