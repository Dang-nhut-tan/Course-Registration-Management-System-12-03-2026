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
from app.test.test_base import driver


MAX_CREDIT_MESSAGE = "Vượt giới hạn 25 tín chỉ trong 1 kỳ."


def hashed_password(password):
    return hashlib.md5(password.strip().encode("utf-8")).hexdigest()


def create_scheduled_course(index, now, faculty, training_program, student_class, room):
    course = Course(
        name=f"MAX COURSE {index} {now}",
        credits=5,
        faculty_id=faculty.id,
    )
    db.session.add(course)
    db.session.flush()

    training_program_course = TrainingProgramCourse(
        training_program_id=training_program.id,
        course_id=course.id,
        semester_no=1,
    )
    db.session.add(training_program_course)

    section = ClassSection(
        name=f"Section {index}",
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
        day_of_week=index + 2,
        start_time=datetime.strptime("07:30", "%H:%M").time(),
        end_time=datetime.strptime("09:30", "%H:%M").time(),
    )
    db.session.add(schedule)

    return course.name


def seed_max_credit_data():
    now = int(time.time())
    student_code = f"MAX{now}"

    with app.app_context():
        faculty = Faculty(
            name=f"Faculty {now}",
            registration_start_date=datetime.now() - timedelta(days=1),
            registration_deadline=datetime.now() + timedelta(days=30),
        )
        db.session.add(faculty)
        db.session.flush()

        major = Major(name=f"Major {now}", faculty_id=faculty.id)
        db.session.add(major)
        db.session.flush()

        student_class = StudentClass(
            code=f"CLS{now}",
            name=f"Class {now}",
            school_year="2025",
            major_id=major.id,
        )
        db.session.add(student_class)
        db.session.flush()

        student = Student(
            student_code=student_code,
            name="SEL Student",
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

        campus = Campus(name=f"Campus {now}")
        db.session.add(campus)
        db.session.flush()

        room = Room(
            name=f"Room {now}",
            room_type="theory",
            capacity=100,
            campus_id=campus.id,
        )
        db.session.add(room)
        db.session.flush()

        training_program = TrainingProgram(
            name=f"Program {now}",
            major_id=major.id,
            school_year="2025",
            max_credits_per_semester=25,
        )
        db.session.add(training_program)
        db.session.flush()

        course_names = [
            create_scheduled_course(
                index,
                now,
                faculty,
                training_program,
                student_class,
                room,
            )
            for index in range(6)
        ]

        db.session.commit()

    return student_code, course_names


def student_login(driver, student_code):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(student_code, "123456")
    time.sleep(1)


def register_course(registration_page, course_name):
    registration_page.open_page(course_query=course_name)
    registration_page.register_course(course_name)
    time.sleep(1)


def test_student_cannot_register_over_25_credits(driver):
    student_code, course_names = seed_max_credit_data()

    student_login(driver, student_code)
    registration_page = StudentRegistrationPage(driver)

    for course_name in course_names[:5]:
        register_course(registration_page, course_name)

    register_course(registration_page, course_names[5])
    time.sleep(2)

    assert MAX_CREDIT_MESSAGE in registration_page.get_message()


def test_student_register_maximum_25_credits(driver):

    courses = [
        "Thiết kế giao diện người dùng",
        "An toàn thông tin căn bản",
        "Lập trình dịch vụ Web",
        "Lịch sử Đảng Cộng sản Việt Nam",
        "Nhập môn khoa học máy tính",
        "Pháp luật đại cương",
        "Quản trị học"
    ]

    student_login(driver,"2354050117")
    registration_page = StudentRegistrationPage(driver)

    for course_name in courses:
        registration_page.open_page(course_query=course_name)
        time.sleep(2)
        registration_page.register_course(course_name)
        time.sleep(2)
        assert (
            "Đăng ký môn học thành công."
            in registration_page.get_message()
        )
    registration_page.open_page()
    time.sleep(2)
    assert registration_page.get_registered_credits() == 25


def test_student_register_24_credits(driver):
    courses = [
        "Mạng máy tính",
        "Đại số tuyến tính",
        "Triết học Mác-Lênin",
        "Phát triển ứng dụng di động",
        "Hệ thống quản lí nguồn lực doanh nghiệp",
        "Điện toán đám mây"
    ]

    student_login(driver,"2354050116")
    registration_page = StudentRegistrationPage(driver)

    for course_name in courses:
        registration_page.open_page(course_query=course_name)
        time.sleep(2)
        registration_page.register_course(course_name)
        time.sleep(2)
        assert (
            "Đăng ký môn học thành công."
            in registration_page.get_message()
        )
    registration_page.open_page()
    time.sleep(2)
    assert registration_page.get_registered_credits() == 24

def test_student_register_26_credits(driver):
    courses = [
        "Tư tưởng Hồ Chí Minh",
        "Toán rời rạc",
        "Giải tích",
        "Điện toán đám mây",
        "Cấu trúc dữ liệu và giải thuật"
    ]

    student_login(driver,"2354050113")
    registration_page = StudentRegistrationPage(driver)

    for course_name in courses[:-1]:
        registration_page.open_page(course_query=course_name)
        time.sleep(2)

        registration_page.register_course(course_name)
        time.sleep(2)
        assert (
            "Đăng ký môn học thành công."
            in registration_page.get_message()
        )

    # REGISTER LAST COURSE
    last_course = courses[-1]

    registration_page.open_page(course_query=last_course)
    time.sleep(2)

    registration_page.register_course(last_course)

    time.sleep(2)

    # ASSERT OVER MAX CREDIT
    assert (
            MAX_CREDIT_MESSAGE
            in registration_page.get_message()
    )

    # ASSERT TOTAL CREDITS STILL 22
    registration_page.open_page()
    time.sleep(2)
    assert registration_page.get_registered_credits() == 22
