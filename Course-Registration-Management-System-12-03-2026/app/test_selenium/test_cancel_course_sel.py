from app.test_selenium.pages.gradePage import GradePage
from app.test_selenium.pages.loginPage import LoginPage
from app.test_selenium.pages.studentRegistrationPage import StudentRegistrationPage
from app.test_selenium.registration_test_data import create_registration_scenario

from app.test.test_base import driver

MIN_CREDITS_MESSAGE = "Không thể hủy vì số tín chỉ sau khi hủy nhỏ hơn 12."
CANCEL_DEADLINE_MESSAGE = "Đã quá hạn hủy môn"
MIDTERM_GRADE_MESSAGE = "Không thể hủy môn vì đã có điểm giữa kỳ"


def student_login(driver, student_code):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(student_code, "123456")


def test_student_cannot_cancel_course_below_minimum_credits(driver):
    scenario = create_registration_scenario(
        "SEL Minimum Credits",
        baseline_credits=9,
        target_enrolled=True,
    )
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(registered_query=scenario.course_name)
    registration_page.cancel_course(scenario.course_name)

    assert MIN_CREDITS_MESSAGE in registration_page.get_message()


def test_student_cannot_cancel_course_after_deadline(driver):
    scenario = create_registration_scenario(
        "SEL Expired Cancellation",
        target_enrolled=True,
        cancel_deadline_passed=True,
    )
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(registered_query=scenario.course_name)
    registration_page.cancel_course(scenario.course_name)

    assert CANCEL_DEADLINE_MESSAGE in registration_page.get_message()

def test_student_cannot_cancel_course_has_midterm_grade(driver):
    scenario = create_registration_scenario(
        "SEL Midterm Grade",
        target_enrolled=True,
    )

    login = LoginPage(driver)
    login.open_page()
    login.login("admin", "admin123", role="admin")
    
    grade_page = GradePage(driver)
    grade_page.open_list()
    grade_page.create_midterm_score(scenario.student_code, "10")
    login.open_page()
    login.login(scenario.student_code, "123456")
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(registered_query=scenario.course_name)
    registration_page.cancel_course(scenario.course_name)

    assert MIDTERM_GRADE_MESSAGE in registration_page.get_message()
