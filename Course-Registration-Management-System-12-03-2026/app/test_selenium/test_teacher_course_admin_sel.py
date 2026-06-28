import time
from app.test_selenium.pages.teacherCoursePage import TeacherCoursePage
from app.test_selenium.pages.teacherPage import TeacherPage
from app.test.test_base import driver


def test_admin_create_teacher_course(driver):
    teacher_name = f"Selenium TC Teacher {int(time.time())}"

    teacher_course_page = TeacherCoursePage(driver)
    # LOGIN ADMIN
    teacher_course_page.admin_login()

    teacher_page = TeacherPage(driver)
    teacher_page.create_teacher(teacher_name)
    time.sleep(1)

    teacher_course_page = TeacherCoursePage(driver)
    teacher_course_page.create_teacher_course()
    time.sleep(1)

    assert teacher_course_page.has_created_message()

    teacher_course_page.edit_teacher_course(teacher_name)
    time.sleep(1)

    assert teacher_course_page.has_saved_message()

    teacher_course_page.delete_teacher_course(teacher_name)
    time.sleep(1)

    assert teacher_course_page.has_deleted_message()
