import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from app.test_selenium.pages.classSectionPage import ClassSectionPage
from app.test_selenium.pages.gradePage import GradePage
from app.test_selenium.pages.loginPage import LoginPage
from app.test_selenium.pages.studentRegistrationPage import StudentRegistrationPage

from app.test.test_base import driver

MIN_CREDITS_MESSAGE = "Không thể hủy vì nếu hủy sẽ có số tín chỉ nhỏ hơn 12."
CANCEL_DEADLINE_MESSAGE = "Đã quá hạn hủy môn"
MIDTERM_GRADE_MESSAGE = "Không thể hủy môn đã có điểm thi giữa kỳ"


def student_login(driver,student_code):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(student_code,"123456")
    time.sleep(2)


def safe_register_course(registration_page,course_name):
    try:
        registration_page.register_course(course_name)
        time.sleep(2)

    except Exception:
        pass


def test_student_cannot_cancel_course_below_minimum_credits(driver):
    course_name = "Quản trị dự án phần mềm"
    student_login(driver,"2354050113")
    registration_page = (StudentRegistrationPage(driver))
    registration_page.open_page(registered_query=course_name)

    time.sleep(2)

    registration_page.cancel_course(course_name)

    time.sleep(2)

    assert (
            MIN_CREDITS_MESSAGE
            in registration_page.get_message()
    )


def test_student_cannot_cancel_course_after_deadline(driver):
    course_name = "Mạng máy tính"
    student_login(driver,"2354050116")

    registration_page = (StudentRegistrationPage(driver))
    registration_page.open_page(course_query=course_name)
    time.sleep(2)
    safe_register_course(registration_page,course_name)

    class_section_page = ClassSectionPage(driver)
    class_section_page.admin_login()

    class_section_page.open_list()
    time.sleep(2)
    class_section_page.click_edit_for_row_containing(course_name)
    time.sleep(2)

    class_section_page.set_value(
        *class_section_page.START_DATE_INPUT,
        "2026-04-30 00:00:00",
    )
    class_section_page.select_value(
        *class_section_page.SCHEDULE_DAY_SELECT,
        "2",
    )
    class_section_page.submit()
    time.sleep(2)

    student_login(driver,"2354050116")
    registration_page.open_page(registered_query=course_name)
    time.sleep(2)
    registration_page.cancel_course(course_name)
    time.sleep(2)
    assert (
            CANCEL_DEADLINE_MESSAGE
            in registration_page.get_message()
    )

def test_student_cannot_cancel_course_has_midterm_grade(driver):
    course_name = "Cơ sở dữ liệu"

    login = LoginPage(driver)
    login.open_page()
    login.login("admin","admin123",role="admin")
    time.sleep(2)
    
    grade_page = GradePage(driver)
    grade_page.open_list()
    time.sleep(2)
    grade_page.click_create()
    time.sleep(2)

    driver.find_element(
        By.ID,
        "s2id_enrollment"
    ).click()

    time.sleep(1)

    search_input = driver.find_element(
        By.CLASS_NAME,
        "select2-input"
    )
    search_input.send_keys(Keys.ARROW_DOWN)
    time.sleep(1)
    search_input.send_keys(Keys.ENTER)
    time.sleep(1)
    driver.find_element(
        By.NAME,
        "midterm_score"
    ).send_keys("10")
    time.sleep(1)
    driver.find_element(
        By.CSS_SELECTOR,
        "input[type='submit']"
    ).click()
    time.sleep(2)
    login.open_page()
    login.login("2354050113","123456")
    time.sleep(2)
    registration_page = (StudentRegistrationPage(driver))
    registration_page.open_page(registered_query=course_name)
    time.sleep(2)
    registration_page.cancel_course(course_name)
    time.sleep(2)

    assert (
        "Không thể hủy môn vì đã có điểm giữa kỳ"
        in registration_page.get_message()
    )
