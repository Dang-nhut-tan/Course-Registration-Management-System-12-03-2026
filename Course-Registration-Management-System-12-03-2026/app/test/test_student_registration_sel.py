import hashlib
import time
from datetime import datetime, timedelta

from app import app, db
from app.model import (
    Campus,
    ClassSection,
    Course,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    Major,
    Room,
    Student,
    StudentClass,
    TrainingProgram,
    TrainingProgramCourse,
    User,
    UserRole,
)
from app.test.pages.loginPage import LoginPage
from app.test.pages.studentRegistrationPage import StudentRegistrationPage
from app.test.test_base import driver


REGISTER_SUCCESS_MESSAGE = "Đăng ký môn học thành công."
CANCEL_SUCCESS_MESSAGE = "Hủy môn học thành công."


def hashed_password(password):
    return hashlib.md5(password.strip().encode("utf-8")).hexdigest()


def seed_registration_selenium_data():
    now = int(time.time())
    student_code = f"SEL{now}"
    course_name = f"SEL Registration Course {now}"

    with app.app_context():
        faculty = Faculty(name=f"SEL Faculty {now}")
        db.session.add(faculty)
        db.session.flush()

        major = Major(name=f"SEL Major {now}", faculty_id=faculty.id)
        db.session.add(major)
        db.session.flush()

        student_class = StudentClass(
            code=f"SELCLS{now}",
            name=f"SEL Class {now}",
            school_year="2025",
            major_id=major.id,
        )
        db.session.add(student_class)
        db.session.flush()

        student = Student(
            student_code=student_code,
            name=f"SEL Student {now}",
            birth_year=2005,
            major_id=major.id,
            class_id=student_class.id,
        )
        user = User(
            student_code=student_code,
            password=hashed_password("123456"),
            role=UserRole.STUDENT,
        )
        campus = Campus(name=f"SEL Campus {now}")
        db.session.add_all([student, user, campus])
        db.session.flush()

        room = Room(
            name=f"SEL Room {now}",
            room_type="theory",
            capacity=50,
            campus_id=campus.id,
        )
        course = Course(
            name=course_name,
            credits=3,
            faculty_id=faculty.id,
        )
        training_program = TrainingProgram(
            name=f"SEL Program {now}",
            major_id=major.id,
            school_year="2025",
            max_credits_per_semester=25,
        )
        db.session.add_all([room, course, training_program])
        db.session.flush()

        training_program_course = TrainingProgramCourse(
            training_program_id=training_program.id,
            course_id=course.id,
            semester_no=2,
        )
        section = ClassSection(
            name=f"SEL Section {now}",
            course_id=course.id,
            student_class_id=student_class.id,
            room_id=room.id,
            semester="2026-1",
            max_students=50,
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=30),
        )
        db.session.add_all([training_program_course, section])
        db.session.commit()

    return student_code, course_name


def cleanup_registration_selenium_data(student_code, course_name):
    with app.app_context():
        course = Course.query.filter_by(name=course_name).first()
        student = Student.query.filter_by(student_code=student_code).first()

        if course:
            section_ids = [
                section.id
                for section in ClassSection.query.filter_by(course_id=course.id).all()
            ]
            if section_ids:
                Enrollment.query.filter(Enrollment.class_section_id.in_(section_ids)).delete(
                    synchronize_session=False
                )
                ClassSection.query.filter(ClassSection.id.in_(section_ids)).delete(
                    synchronize_session=False
                )
            TrainingProgramCourse.query.filter_by(course_id=course.id).delete()
            db.session.delete(course)

        if student:
            User.query.filter_by(student_code=student_code).delete()
            db.session.delete(student)

        db.session.commit()


def test_student_register_and_cancel_course_updates_registered_count(driver):
    student_code, course_name = seed_registration_selenium_data()

    try:
        login = LoginPage(driver)
        login.open_page()
        login.login(student_code, "123456")
        time.sleep(1)

        registration_page = StudentRegistrationPage(driver)
        registration_page.open_page(course_query=course_name)
        time.sleep(1)
        before_register_count = registration_page.get_registered_count()

        registration_page.register_course(course_name)
        time.sleep(1)

        assert registration_page.get_message() == REGISTER_SUCCESS_MESSAGE
        after_register_count = registration_page.get_registered_count()
        assert after_register_count == before_register_count + 1

        registration_page.cancel_course(course_name)
        time.sleep(1)

        assert registration_page.get_message() == CANCEL_SUCCESS_MESSAGE
        after_cancel_count = registration_page.get_registered_count()
        assert after_cancel_count == after_register_count - 1
    finally:
        cleanup_registration_selenium_data(student_code, course_name)
