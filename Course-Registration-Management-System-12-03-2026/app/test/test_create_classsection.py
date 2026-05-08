from Demos.win32ts_logoff_disconnected import username

from app import db
import pytest
from unittest.mock import patch, MagicMock
from app.test.test_base import test_app, test_session
from app.admin import ClassSectionView
from datetime import datetime

from app.model import Campus, ClassSection, ClassSectionType, Course, Room, StudentClass, User, UserRole


class Field:
    def __init__(self, data=None):
        self.data = data

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


def test_auto_link_practice_section(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        campus = Campus(id=1, name="Campus 1")
        theory_room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
        practice_room = Room(id=2, name="TH01", room_type="practice", capacity=50, campus_id=1)
        practice_section = ClassSection(
            id=2,
            name="Practice 1",
            course_id=1,
            room_id=2,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 5, 1),
            section_type=ClassSectionType.PRACTICE,
        )
        form = MagicMock()
        form._fields = {
            "course": Field(course),
            "student_class": Field(None),
            "semester": Field("2026-1"),
            "section_type": Field(ClassSectionType.THEORY),
            "linked_section": Field(None),
        }

        test_session.add_all([course, campus, theory_room, practice_room, practice_section])
        test_session.commit()

        test_admin.auto_link_practice_section(form)

        assert form._fields["linked_section"].data == practice_section


def test_auto_link_practice_section_prefers_practice_room(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        campus = Campus(id=1, name="Campus 1")
        theory_room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
        practice_room = Room(id=2, name="TH01", room_type="practice", capacity=50, campus_id=1)
        theory_room_section = ClassSection(
            id=2,
            name="Practice 1",
            course_id=1,
            room_id=1,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 5, 1),
            section_type=ClassSectionType.PRACTICE,
        )
        practice_room_section = ClassSection(
            id=3,
            name="Practice 2",
            course_id=1,
            room_id=2,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 5, 1),
            section_type=ClassSectionType.PRACTICE,
        )
        form = MagicMock()
        form._fields = {
            "course": Field(course),
            "student_class": Field(None),
            "semester": Field("2026-1"),
            "section_type": Field(ClassSectionType.THEORY),
            "linked_section": Field(None),
        }

        test_session.add_all([
            course,
            campus,
            theory_room,
            practice_room,
            theory_room_section,
            practice_room_section,
        ])
        test_session.commit()

        test_admin.auto_link_practice_section(form)

        assert form._fields["linked_section"].data == practice_room_section


def test_class_section_name_uses_student_class(test_admin):
    student_class = StudentClass(code="DH23IM01")
    course = Course(name="Course 1")
    section = ClassSection()
    form = MagicMock()
    form._fields = {
        "student_class": Field(student_class),
        "course": Field(course),
    }

    test_admin.update_section_name(form, section)

    assert section.name == "DH23IM01"
