import time

from app.test.pages.classSectionPage import ClassSectionPage
from app.test.pages.coursePage import CoursePage
from app.test.pages.loginPage import LoginPage
from app.test.pages.roomPage import RoomPage
from app.test.pages.teacherCoursePage import TeacherCoursePage
from app.test.pages.teacherPage import TeacherPage
from app.test.test_base import driver, test_app


def admin_login(driver):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login("admin", "admin123", role="admin")
    time.sleep(1)


def create_course(driver, course_name):
    CoursePage(driver).create_course(course_name)
    time.sleep(1)


def create_teacher(driver, teacher_name):
    TeacherPage(driver).create_teacher(teacher_name)
    time.sleep(1)


def create_teacher_course(driver):
    TeacherCoursePage(driver).create_teacher_course(course_index=-1)
    time.sleep(1)


def create_room(driver, room_name, room_type):
    RoomPage(driver).create_room(room_name, room_type=room_type)
    time.sleep(1)


def prepare_classsection_data(driver, prefix):
    now = int(time.time())
    course_name = f"{prefix} Course {now}"
    teacher_name = f"{prefix} Teacher {now}"
    theory_room = f"{prefix}-LT-{now}"
    practice_room = f"{prefix}-TH-{now}"

    create_course(driver, course_name)
    create_teacher(driver, teacher_name)
    create_teacher_course(driver)
    create_room(driver, practice_room, "practice")
    create_room(driver, theory_room, "theory")

    return course_name, theory_room, practice_room


def fill_classsection_form(
    driver,
    course_name,
    room_name,
    max_students="40",
    start_time="07:30",
    end_time="12:00",
    start_date_value="2026-08-01 00:00:00",
    end_date_value="2026-12-31 00:00:00",
):
    ClassSectionPage(driver).fill_classsection_form(
        course_name,
        room_name,
        max_students=max_students,
        start_time=start_time,
        end_time=end_time,
        start_date_value=start_date_value,
        end_date_value=end_date_value,
    )
    time.sleep(1)


def submit_form(driver):
    ClassSectionPage(driver).submit()
    time.sleep(1)


def assert_create_failed(driver):
    assert ClassSectionPage(driver).create_failed()


def test_admin_create_classsection_with_auto_teacher_and_practice(driver):
    now = int(time.time())
    course_name = f"SEL ClassSection Course {now}"
    teacher_name = f"SEL ClassSection Teacher {now}"
    theory_room = f"SEL-LT-{now}"
    practice_room = f"SEL-TH-{now}"

    admin_login(driver)
    create_course(driver, course_name)
    create_teacher(driver, teacher_name)
    create_teacher_course(driver)
    create_room(driver, practice_room, "practice")
    create_room(driver, theory_room, "theory")

    fill_classsection_form(driver, course_name, theory_room)
    submit_form(driver)

    classsection_page = ClassSectionPage(driver)
    assert classsection_page.has_created_message()

    classsection_page.edit_max_students(course_name, "45")
    time.sleep(1)

    assert classsection_page.has_saved_message()

    classsection_page.delete_classsection(course_name)
    time.sleep(1)

    assert classsection_page.has_deleted_message()


def test_classsection_rejects_max_students_over_50(driver):
    admin_login(driver)
    course_name, theory_room, practice_room = prepare_classsection_data(driver, "SEL Max")

    fill_classsection_form(driver, course_name, theory_room, max_students="51")
    submit_form(driver)

    assert_create_failed(driver)


def test_classsection_rejects_invalid_schedule_time(driver):
    admin_login(driver)
    course_name, theory_room, practice_room = prepare_classsection_data(driver, "SEL Time")

    fill_classsection_form(
        driver,
        course_name,
        theory_room,
        start_time="12:00",
        end_time="07:30",
    )
    submit_form(driver)

    assert_create_failed(driver)


def test_classsection_rejects_invalid_date_range(driver):
    admin_login(driver)
    course_name, theory_room, practice_room = prepare_classsection_data(driver, "SEL Date")

    fill_classsection_form(
        driver,
        course_name,
        theory_room,
        start_date_value="2026-12-31 00:00:00",
        end_date_value="2026-08-01 00:00:00",
    )
    submit_form(driver)

    assert_create_failed(driver)
