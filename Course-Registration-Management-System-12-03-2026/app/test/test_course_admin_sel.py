import time

from app.test.pages.coursePage import CoursePage
from app.test.pages.loginPage import LoginPage
from app.test.test_base import driver, test_app


def test_admin_create_course(driver):
    course_name = f"Selenium Course {int(time.time())}"
    edited_course_name = f"{course_name} Edited"

    login = LoginPage(driver=driver)
    login.open_page()
    login.login("admin", "admin123", role="admin")
    time.sleep(1)

    course_page = CoursePage(driver)
    course_page.click_create()
    course_page.fill_course_form(course_name)
    course_page.submit()
    time.sleep(1)

    assert course_page.has_created_message()

    course_page.edit_course_name(course_name, edited_course_name)
    time.sleep(1)

    assert course_page.has_saved_message()

    course_page.delete_course(edited_course_name)
    time.sleep(1)

    assert course_page.has_deleted_message()
