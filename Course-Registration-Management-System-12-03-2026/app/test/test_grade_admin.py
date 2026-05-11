from unittest.mock import MagicMock

from app import db
from app.admin import GradeView
from app.model import ClassSection, Course, Enrollment, Grade, Student
from app.test.test_base import test_app


def test_enrollment_display_text_includes_student_course_section_and_semester():
    student = Student(student_code="2354050113", name="Nguyen Van A")
    course = Course(id=1, name="Software Testing", credits=3, faculty_id=1)
    section = ClassSection(id=1, name="DH23IM01", semester="2025-2")
    section.course = course

    enrollment = Enrollment(id=9, student_code="2354050113")
    enrollment.student = student
    enrollment.class_section = section

    display_text = str(enrollment)

    assert "2354050113" in display_text
    assert "Nguyen Van A" in display_text
    assert "Software Testing" in display_text
    assert "DH23IM01" in display_text
    assert "2025-2" in display_text


def test_grade_admin_sets_default_graded_at_when_blank(test_app):
    with test_app.app_context():
        view = GradeView(Grade, db.session)
        grade = Grade()
        form = MagicMock()

        view.on_model_change(form, grade, is_created=True)

        assert grade.graded_at is not None
