from app import db
import pytest
from unittest.mock import patch, MagicMock
from app.test.test_base import test_app, test_session
from app.admin import ClassSectionView, CourseView, TeacherView
from datetime import datetime, time

from app.model import Campus, ClassSection, ClassSectionType, Course, Room, Schedule, StudentClass, Teacher, TeacherCourse, User, UserRole


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


def test_teacher_form_only_edits_name():
    teacher_admin = TeacherView(Teacher, db.session)

    assert teacher_admin.form_columns == ("name",)


def test_course_form_does_not_edit_teacher_courses():
    course_admin = CourseView(Course, db.session)

    assert course_admin.form_columns == ("faculty", "name", "credits", "is_shared")


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


def test_on_model_change_auto_fills_teacher_and_room(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        campus = Campus(id=1, name="Campus 1")
        teacher = Teacher(id=1, name="Teacher 1", faculty_id=1)
        room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
        form = MagicMock()
        form._fields = {
            "course": Field(course),
            "student_class": Field(None),
            "semester": Field("2026-1"),
            "section_type": Field(ClassSectionType.THEORY),
        }
        section = ClassSection(course=course, semester="2026-1", section_type=ClassSectionType.THEORY)

        test_session.add_all([course, campus, teacher, room])
        test_session.commit()

        test_admin.on_model_change(form, section, True)

        assert section.teacher == teacher
        assert section.room == room


def make_class_section_form(**overrides):
    data = {
        "course": Course(id=1, name="Course 1", credits=3, faculty_id=1),
        "student_class": StudentClass(id=1, code="DH23IM01"),
        "teacher": None,
        "room": None,
        "linked_section": None,
        "semester": "2026-1",
        "schedule_day": "2",
        "schedule_start_time": "07:30",
        "schedule_end_time": "12:00",
        "section_type": ClassSectionType.THEORY,
        "max_students": 50,
        "start_date": datetime(2026, 5, 1),
        "end_date": datetime(2026, 8, 1),
    }
    data.update(overrides)

    form = MagicMock()
    form._fields = {
        key: Field(value)
        for key, value in data.items()
    }
    return form


def test_validate_class_section_rejects_invalid_semester(test_app, test_admin):
    with test_app.test_request_context():
        form = make_class_section_form(semester="uedfhuiwqfe")

        assert test_admin.validate_class_section_form(form) is False


def test_validate_class_section_rejects_invalid_dates(test_app, test_admin):
    with test_app.test_request_context():
        form = make_class_section_form(
            start_date=datetime(2026, 8, 1),
            end_date=datetime(2026, 5, 1),
        )

        assert test_admin.validate_class_section_form(form) is False


def test_validate_class_section_rejects_invalid_schedule_day(test_app, test_admin):
    with test_app.test_request_context():
        form = make_class_section_form(schedule_day="abc")

        assert test_admin.validate_class_section_form(form) is False


def test_validate_class_section_rejects_invalid_schedule_time(test_app, test_admin):
    with test_app.test_request_context():
        form = make_class_section_form(
            schedule_start_time="12:00",
            schedule_end_time="07:30",
        )

        assert test_admin.validate_class_section_form(form) is False


def test_teacher_unavailable_reason_names_missing_teacher_course(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        form = make_class_section_form(course=course)
        test_session.add(course)
        test_session.commit()

        reason = test_admin.get_teacher_unavailable_reason(form)

        assert "Course 1" in reason
        assert "Teacher Course" in reason


def test_teacher_unavailable_reason_names_busy_teachers(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        campus = Campus(id=1, name="Campus 1")
        room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
        teacher = Teacher(id=1, name="Teacher 1", faculty_id=1)
        busy_section = ClassSection(
            id=1,
            name="Busy",
            course_id=1,
            teacher_id=1,
            room_id=1,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 8, 1),
            section_type=ClassSectionType.THEORY,
        )
        busy_schedule = Schedule(
            class_section_id=1,
            day_of_week=2,
            start_time=time(7, 30),
            end_time=time(12, 0),
        )
        form = make_class_section_form(course=course)
        test_session.add_all([
            course,
            campus,
            room,
            teacher,
            TeacherCourse(teacher_id=1, course_id=1),
            busy_section,
            busy_schedule,
        ])
        test_session.commit()

        reason = test_admin.get_teacher_unavailable_reason(form)

        assert "đều bận" in reason
        assert "Teacher 1" in reason


def test_class_section_schedule_time_is_read_from_form(test_app, test_admin):
    with test_app.test_request_context():
        form = make_class_section_form(
            schedule_start_time="07:30",
            schedule_end_time="12:00",
        )

        assert test_admin.get_schedule_start_time_from_form(form) == time(7, 30)
        assert test_admin.get_schedule_end_time_from_form(form) == time(12, 0)


def test_after_model_change_saves_selected_schedule_time(test_app, test_session, test_admin):
    with test_app.app_context():
        section = ClassSection(
            id=1,
            name="DH23IM01",
            course_id=1,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 8, 1),
            section_type=ClassSectionType.THEORY,
        )
        form = make_class_section_form(
            schedule_day="3",
            schedule_start_time="07:30",
            schedule_end_time="12:00",
        )

        test_session.add(section)
        test_session.commit()

        test_admin.after_model_change(form, section, True)

        schedule = Schedule.query.filter_by(class_section_id=section.id).first()
        assert schedule.day_of_week == 3
        assert schedule.start_time == time(7, 30)
        assert schedule.end_time == time(12, 0)


def test_after_model_change_creates_and_links_practice_section(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        campus = Campus(id=1, name="Campus 1")
        teacher = Teacher(id=1, name="Teacher 1", faculty_id=1)
        theory_room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
        practice_room = Room(id=2, name="TH01", room_type="practice", capacity=50, campus_id=1)
        section = ClassSection(
            id=1,
            name="DH23IM01",
            course_id=1,
            student_class_id=1,
            teacher_id=1,
            room_id=1,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 8, 1),
            section_type=ClassSectionType.THEORY,
        )
        form = make_class_section_form(
            course=course,
            teacher=teacher,
            room=theory_room,
            schedule_day="2",
            schedule_start_time="07:30",
            schedule_end_time="12:00",
        )

        test_session.add_all([
            course,
            campus,
            teacher,
            TeacherCourse(teacher_id=1, course_id=1),
            theory_room,
            practice_room,
            section,
        ])
        test_session.commit()

        test_admin.after_model_change(form, section, True)

        assert section.linked_section is not None
        assert section.linked_section.section_type == ClassSectionType.PRACTICE
        assert section.linked_section.course_id == section.course_id
        assert section.linked_section.room_id == practice_room.id

        practice_schedule = Schedule.query.filter_by(
            class_section_id=section.linked_section.id,
        ).first()
        assert practice_schedule is not None
        assert (
            practice_schedule.day_of_week,
            practice_schedule.start_time,
            practice_schedule.end_time,
        ) == (2, time(13, 0), time(17, 30))


def test_after_model_change_uses_practice_room_in_same_campus(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        campus_1 = Campus(id=1, name="Campus 1")
        campus_2 = Campus(id=2, name="Campus 2")
        teacher = Teacher(id=1, name="Teacher 1", faculty_id=1)
        theory_room = Room(id=1, name="C201", room_type="theory", capacity=50, campus_id=2)
        wrong_campus_practice_room = Room(id=2, name="TH01", room_type="practice", capacity=50, campus_id=1)
        same_campus_practice_room = Room(id=3, name="TH03", room_type="practice", capacity=50, campus_id=2)
        section = ClassSection(
            id=1,
            name="DH23IM01",
            course_id=1,
            student_class_id=1,
            teacher_id=1,
            room_id=1,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 8, 1),
            section_type=ClassSectionType.THEORY,
        )
        form = make_class_section_form(
            course=course,
            teacher=teacher,
            room=theory_room,
            schedule_day="2",
            schedule_start_time="07:30",
            schedule_end_time="12:00",
        )

        test_session.add_all([
            course,
            campus_1,
            campus_2,
            teacher,
            TeacherCourse(teacher_id=1, course_id=1),
            theory_room,
            wrong_campus_practice_room,
            same_campus_practice_room,
            section,
        ])
        test_session.commit()

        test_admin.after_model_change(form, section, True)

        assert section.linked_section.room_id == same_campus_practice_room.id


def test_after_model_change_creates_morning_practice_for_afternoon_theory(test_app, test_session, test_admin):
    with test_app.app_context():
        course = Course(id=1, name="Course 1", credits=3, faculty_id=1)
        campus = Campus(id=1, name="Campus 1")
        teacher = Teacher(id=1, name="Teacher 1", faculty_id=1)
        theory_room = Room(id=1, name="A101", room_type="theory", capacity=50, campus_id=1)
        practice_room = Room(id=2, name="TH01", room_type="practice", capacity=50, campus_id=1)
        section = ClassSection(
            id=1,
            name="DH23IM01",
            course_id=1,
            student_class_id=1,
            teacher_id=1,
            room_id=1,
            semester="2026-1",
            max_students=50,
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 8, 1),
            section_type=ClassSectionType.THEORY,
        )
        form = make_class_section_form(
            course=course,
            teacher=teacher,
            room=theory_room,
            schedule_day="4",
            schedule_start_time="13:00",
            schedule_end_time="17:30",
        )

        test_session.add_all([
            course,
            campus,
            teacher,
            TeacherCourse(teacher_id=1, course_id=1),
            theory_room,
            practice_room,
            section,
        ])
        test_session.commit()

        test_admin.after_model_change(form, section, True)

        practice_schedule = Schedule.query.filter_by(
            class_section_id=section.linked_section.id,
        ).first()
        assert (
            practice_schedule.day_of_week,
            practice_schedule.start_time,
            practice_schedule.end_time,
        ) == (4, time(7, 30), time(12, 0))
