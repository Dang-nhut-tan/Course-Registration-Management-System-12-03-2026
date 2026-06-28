
import time
from app.test_selenium.pages.loginPage import LoginPage
from app.test_selenium.pages.studentRegistrationPage import StudentRegistrationPage
from app.test.test_base import driver


REGISTER_SUCCESS_MESSAGE = "Đăng ký môn học thành công."
CANCEL_SUCCESS_MESSAGE = "Hủy môn học thành công."
ALREADY_REGISTERED_MESSAGE = "đã được đăng ký rồi"

def student_login(driver, student_code):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(student_code,"123456")
    time.sleep(1)

def safe_register_course(registration_page,course_name):
    try:
        registration_page.register_course(course_name)
        time.sleep(2)
    except Exception:
        pass


def test_student_register_course_updates_timetable_and_grade_page(driver):
    course_name = "Khóa luận tốt nghiệp"
    student_login(driver,"2354050113")
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(course_query=course_name)
    time.sleep(2)

    before_register_count = registration_page.get_registered_count()
    safe_register_course(registration_page,course_name)
    time.sleep(2)
    assert (
            REGISTER_SUCCESS_MESSAGE
            in registration_page.get_message()
    )

    after_register_count = registration_page.get_registered_count()
    assert (
            after_register_count
            == before_register_count + 1
    )

    driver.get("http://127.0.0.1:5000/timetable")
    time.sleep(2)
    assert (
        course_name
        in driver.page_source
    )

    driver.get("http://127.0.0.1:5000/grades")
    time.sleep(2)
    assert (
        course_name
        in driver.page_source
    )



def test_student_cancel_course_removes_timetable_and_grade_page(driver):
    course_name = "Kiến trúc phần mềm"
    student_login(driver,"2354050113")
    registration_page = StudentRegistrationPage(driver)

    # REGISTER COURSE FIRST
    registration_page.open_page(course_query=course_name)
    time.sleep(2)
    safe_register_course(registration_page,course_name)
    time.sleep(2)
    # OPEN REGISTERED COURSES
    registration_page.open_page(registered_query=course_name)
    time.sleep(2)
    # COUNT BEFORE CANCEL
    before_cancel_count = registration_page.get_registered_count()
    # CANCEL COURSE
    registration_page.cancel_course(course_name)
    time.sleep(2)
    # ASSERT CANCEL SUCCESS
    assert (
        CANCEL_SUCCESS_MESSAGE
        in registration_page.get_message()
    )

    # ASSERT COUNT UPDATED
    after_cancel_count = registration_page.get_registered_count()

    assert (
            after_cancel_count
            == before_cancel_count - 1
    )
    driver.get("http://127.0.0.1:5000/timetable")

    time.sleep(2)

    assert (
        course_name
        not in driver.page_source
    )

    driver.get("http://127.0.0.1:5000/grades")

    time.sleep(2)

    assert (
        course_name
        not in driver.page_source
    )

def test_student_cannot_register_registered_course(driver):
    course_name = "Lịch sử Đảng Cộng sản Việt Nam"
    student_login(driver,"2354050113")
    registration_page = StudentRegistrationPage(driver)


    registration_page.open_page(course_query=course_name)
    time.sleep(2)
    registration_page.register_course(course_name)
    time.sleep(2)

    registration_page.open_page( course_query=course_name)
    time.sleep(2)
    registration_page.driver.find_element(
        *registration_page.SECOND_ROW_REGISTER_BUTTON
    ).click()
    time.sleep(2)

    assert (
        ALREADY_REGISTERED_MESSAGE
        in registration_page.get_message()
    )

