import time

from app.test.pages.loginPage import LoginPage
from app.test.pages.teacherPage import TeacherPage
from app.test.test_base import driver, test_app


def test_admin_create_teacher(driver):
    teacher_name = f"Selenium Teacher {int(time.time())}"
    edited_teacher_name = f"{teacher_name} Edited"

    login = LoginPage(driver=driver)
    login.open_page()
    login.login("admin", "admin123", role="admin")
    time.sleep(1)

    teacher_page = TeacherPage(driver)
    teacher_page.create_teacher(teacher_name)
    time.sleep(1)

    assert teacher_page.has_created_message()

    teacher_page.edit_teacher_name(teacher_name, edited_teacher_name)
    time.sleep(1)

    assert teacher_page.has_saved_message()

    teacher_page.delete_teacher(edited_teacher_name)
    time.sleep(1)

    assert teacher_page.has_deleted_message()
