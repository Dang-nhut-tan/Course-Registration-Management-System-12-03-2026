from datetime import datetime, timedelta
from app import db
import pytest
from app.admin import CampusView, RoomView, CourseView
from app.model import Campus, ClassSection, Room, Course, CoursePrerequisite, CourseMajor
from app.test.test_base import test_app, test_session


@pytest.fixture
def setup_campus_room(test_session, test_app):
    with test_app.app_context():
        campus = Campus(id=1, name="Cơ sở 1")
        room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
        test_session.add_all([campus, room])
        test_session.commit()
        return campus, room


@pytest.fixture
def setup_course_data(test_session, test_app):
    with test_app.app_context():
        from app.model import Faculty
        faculty = Faculty(id=1, name="CNTT")
        course = Course(id=10, name="Lập trình cơ sở dữ liệu", credits=3, faculty_id=1)
        test_session.add_all([faculty, course])
        test_session.commit()
        return course


def test_delete_room(setup_campus_room, test_app, test_session):
    campus, room = setup_campus_room
    view = RoomView(Room, test_session)

    with test_app.app_context():
        test_session.add(room)
        actual_result = view.delete_model(room)
        assert actual_result is True
        assert db.session.get(Room, 1) is None


def test_delete_room_used_by_section(setup_campus_room, test_app, test_session):
    campus, room = setup_campus_room

    with test_app.app_context():
        test_session.add(room)
        section = ClassSection(
            id=1, name="B201", course_id=None, room_id=1,
            semester="2026-1", max_students=40,
            start_date=datetime.now(), end_date=datetime.now() + timedelta(days=30)
        )
        test_session.add(section)
        test_session.commit()

        view = RoomView(Room, test_session)

        with test_app.test_request_context():
            test_session.add(room)
            actual_result = view.delete_model(room)

        assert actual_result is False
        assert db.session.get(Room, 1) is not None


def test_delete_campus(setup_campus_room, test_app, test_session):
    with test_app.app_context():
        campus = Campus(id=2, name="Cơ sở 2")
        test_session.add(campus)
        test_session.commit()

        view = CampusView(Campus, test_session)
        actual_result = view.delete_model(campus)
        assert actual_result is True


def test_delete_campus_with_rooms(setup_campus_room, test_app, test_session):
    campus, room = setup_campus_room

    with test_app.app_context():
        test_session.add(campus)
        view = CampusView(Campus, test_session)

        with test_app.test_request_context():
            test_session.add(campus)
            actual_result = view.delete_model(campus)

        assert actual_result is False
        assert db.session.get(Campus, 1) is not None


def test_delete_course(setup_course_data, test_app, test_session):
    course = setup_course_data
    with test_app.app_context():
        test_session.add(course)
        view = CourseView(Course, test_session)
        actual_result = view.delete_model(course)
        assert actual_result is True


def test_delete_course_with_section(setup_course_data, test_app, test_session):
    course = setup_course_data
    with test_app.app_context():
        test_session.add(course)
        section = ClassSection(
            id=2, name="Cơ sở lập trình", course_id=course.id,
            semester="2026-1", max_students=30,
            start_date=datetime.now(), end_date=datetime.now() + timedelta(days=30)
        )
        test_session.add(section)
        test_session.commit()

        view = CourseView(Course, test_session)

        with test_app.test_request_context():
            test_session.add(course)
            actual_result = view.delete_model(course)

        assert actual_result is False


def test_delete_course_as_prerequisite(setup_course_data, test_app, test_session):
    course = setup_course_data

    with test_app.app_context():
        test_session.add(course)
        course_prerequisite = Course(id=11, name="Cơ sở dữ liệu", credits=3, faculty_id=1)
        prerequisite = CoursePrerequisite(course_id=11, prerequisite_id=10)
        test_session.add_all([course_prerequisite, prerequisite])
        test_session.commit()

        view = CourseView(Course, test_session)

        with test_app.test_request_context():
            test_session.add(course)
            actual_result = view.delete_model(course)

        assert actual_result is False

def test_delete_course_in_major_program(setup_course_data, test_app, test_session):
    course = setup_course_data
    with test_app.app_context():
        test_session.add(course)
        major_link = CourseMajor(course_id=course.id, major_id=1)
        test_session.add(major_link)
        test_session.commit()

        view = CourseView(Course, test_session)

        with test_app.test_request_context():
            test_session.add(course)
            actual_result = view.delete_model(course)

        assert actual_result is False
