import hashlib
import time
from datetime import datetime, timedelta

from app import app, db
from app.model import (
    Campus,
    ClassSection,
    Course,
    Faculty,
    Major,
    Room,
    Schedule,
    Student,
    StudentClass,
    TrainingProgram,
    TrainingProgramCourse,
    User,
    UserRole,
)
from app.test_selenium.pages.loginPage import LoginPage
from app.test_selenium.pages.studentRegistrationPage import StudentRegistrationPage
from app.test.test_base import driver, test_app


SCHEDULE_CONFLICT_MESSAGE = "Trùng lịch học"


def hashed_password(password):
    return hashlib.md5(password.strip().encode("utf-8")).hexdigest()


def create_section(course, student_class, room, name):
    section = ClassSection(
        name=name,
        course_id=course.id,
        student_class_id=student_class.id,
        room_id=room.id,
        semester="2026-1",
        max_students=50,
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(days=30),
    )
    db.session.add(section)
    db.session.flush()

    schedule = Schedule(
        class_section_id=section.id,
        day_of_week=2,
        start_time=datetime.strptime("07:30", "%H:%M").time(),
        end_time=datetime.strptime("09:30", "%H:%M").time(),
    )
    db.session.add(schedule)


def seed_schedule_conflict_data():
    now = int(time.time())
    student_code = f"SEL{now}"
    course_1_name = f"SEL Schedule Course 1 {now}"
    course_2_name = f"SEL Schedule Course 2 {now}"

    with app.app_context():
        faculty = Faculty(
            name=f"SEL Faculty {now}",
            registration_start_date=datetime.now() - timedelta(days=1),
            registration_deadline=datetime.now() + timedelta(days=30),
        )
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
        db.session.add_all([student, user])

        campus = Campus(name=f"SEL Campus {now}")
        db.session.add(campus)
        db.session.flush()

        room = Room(
            name=f"SEL Room {now}",
            room_type="theory",
            capacity=50,
            campus_id=campus.id,
        )
        db.session.add(room)
        db.session.flush()

        training_program = TrainingProgram(
            name=f"SEL Program {now}",
            major_id=major.id,
            school_year="2025",
            max_credits_per_semester=25,
        )
        db.session.add(training_program)
        db.session.flush()

        course_1 = Course(name=course_1_name, credits=3, faculty_id=faculty.id)
        course_2 = Course(name=course_2_name, credits=3, faculty_id=faculty.id)
        db.session.add_all([course_1, course_2])
        db.session.flush()

        db.session.add_all(
            [
                TrainingProgramCourse(
                    training_program_id=training_program.id,
                    course_id=course_1.id,
                    semester_no=2,
                ),
                TrainingProgramCourse(
                    training_program_id=training_program.id,
                    course_id=course_2.id,
                    semester_no=2,
                ),
            ]
        )

        create_section(course_1, student_class, room, f"SEL Section 1 {now}")
        create_section(course_2, student_class, room, f"SEL Section 2 {now}")
        db.session.commit()

    return student_code, course_1_name, course_2_name


def student_login(driver, student_code):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(student_code, "123456")
    time.sleep(1)


def register_course(registration_page, course_name, wait_time=2):
    registration_page.open_page(course_query=course_name)
    time.sleep(wait_time)
    registration_page.register_course(course_name)
    time.sleep(wait_time)


def assert_schedule_conflict(registration_page):
    assert SCHEDULE_CONFLICT_MESSAGE in registration_page.get_message()


def test_student_cannot_register_schedule_conflict01(driver):
    student_code, course_1_name, course_2_name = seed_schedule_conflict_data()

    student_login(driver, student_code)

    registration_page = StudentRegistrationPage(driver)
    register_course(registration_page, course_1_name, wait_time=3)
    register_course(registration_page, course_2_name, wait_time=1)

    assert_schedule_conflict(registration_page)


def test_student_cannot_register_schedule_conflict02(driver):
    course_1 = "Triết học Mác-Lênin"
    course_2 = "Tư tưởng Hồ Chí Minh"

    student_login(driver, "2354050113")

    registration_page = StudentRegistrationPage(driver)
    register_course(registration_page, course_1)
    register_course(registration_page, course_2)

    assert_schedule_conflict(registration_page)


def test_student_cannot_register_schedule_conflict03(driver):
    course_1 = "Triết học Mác-Lênin"
    course_2 = "Kiến trúc phần mềm"

    student_login(driver, "2354050113")

    registration_page = StudentRegistrationPage(driver)
    register_course(registration_page, course_1)
    register_course(registration_page, course_2)

    assert_schedule_conflict(registration_page)
