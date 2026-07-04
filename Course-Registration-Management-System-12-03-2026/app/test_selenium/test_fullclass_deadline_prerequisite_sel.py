from app.test.test_base import driver
from app.test_selenium.pages.loginPage import LoginPage
from app.test_selenium.pages.studentRegistrationPage import StudentRegistrationPage
from app.test_selenium.registration_test_data import create_registration_scenario


FULL_CLASS_MESSAGE = "Lớp học phần đã hết chỗ."


def student_login(driver, student_code):
    login = LoginPage(driver)
    login.open_page()
    login.login(student_code, "123456")


def test_student_cannot_register_full_class(driver):
    scenario = create_registration_scenario(
        "SEL Full Class",
        target_capacity=0,
    )
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(course_query=scenario.course_name)
    registration_page.register_course(scenario.course_name)

    assert FULL_CLASS_MESSAGE in registration_page.get_message()


def test_student_cannot_register_without_prerequisite(driver):
    scenario = create_registration_scenario(
        "SEL Missing Prerequisite",
        missing_prerequisite=True,
    )
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(course_query=scenario.course_name)
    registration_page.register_course(scenario.course_name)

    assert f"Thiếu tiên quyết: {scenario.prerequisite_name}" in registration_page.get_message()


def test_student_cannot_register_after_deadline(driver):
    scenario = create_registration_scenario(
        "SEL Registration Deadline",
        registration_deadline_passed=True,
    )
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(course_query=scenario.course_name)

    assert not registration_page.has_open_course(scenario.course_name)
