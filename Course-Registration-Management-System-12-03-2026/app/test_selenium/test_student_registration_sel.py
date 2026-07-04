
from app.test_selenium.pages.loginPage import LoginPage
from app.test_selenium.pages.studentRegistrationPage import StudentRegistrationPage
from app.test_selenium.pages.studentAcademicPage import StudentAcademicPage
from app.test_selenium.registration_test_data import create_registration_scenario
from app.test.test_base import driver


REGISTER_SUCCESS_MESSAGE = "Đăng ký môn học thành công."
CANCEL_SUCCESS_MESSAGE = "Hủy môn học thành công."
ALREADY_REGISTERED_MESSAGE = "đã được đăng ký rồi"

def student_login(driver, student_code):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(student_code, "123456")


def test_student_register_course_updates_timetable_and_grade_page(driver):
    scenario = create_registration_scenario("SEL Register Course")
    course_name = scenario.course_name
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(course_query=course_name)

    before_register_count = registration_page.get_registered_count()
    registration_page.register_course(course_name)
    assert (
            REGISTER_SUCCESS_MESSAGE
            in registration_page.get_message()
    )

    after_register_count = registration_page.get_registered_count()
    assert (
            after_register_count
            == before_register_count + 1
    )

    academic_page = StudentAcademicPage(driver)
    academic_page.open_timetable()
    assert academic_page.has_course(course_name)

    academic_page.open_grades()
    assert academic_page.has_course(course_name)



def test_student_cancel_course_removes_timetable_and_grade_page(driver):
    scenario = create_registration_scenario(
        "SEL Cancel Course",
        baseline_credits=12,
    )
    course_name = scenario.course_name
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)

    # REGISTER COURSE FIRST
    registration_page.open_page(course_query=course_name)
    registration_page.register_course(course_name)
    assert REGISTER_SUCCESS_MESSAGE in registration_page.get_message()
    # OPEN REGISTERED COURSES
    registration_page.open_page(registered_query=course_name)
    # COUNT BEFORE CANCEL
    before_cancel_count = registration_page.get_registered_count()
    # CANCEL COURSE
    registration_page.cancel_course(course_name)
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
    academic_page = StudentAcademicPage(driver)
    academic_page.open_timetable()
    assert academic_page.does_not_have_course(course_name)

    academic_page.open_grades()
    assert academic_page.does_not_have_course(course_name)

def test_student_cannot_register_registered_course(driver):
    scenario = create_registration_scenario(
        "SEL Duplicate Registration",
        target_section_count=2,
    )
    course_name = scenario.course_name
    student_login(driver, scenario.student_code)
    registration_page = StudentRegistrationPage(driver)


    registration_page.open_page(course_query=course_name)
    registration_page.register_course(course_name)
    assert REGISTER_SUCCESS_MESSAGE in registration_page.get_message()

    registration_page.open_page(course_query=course_name)
    registration_page.register_course_from_result(2)

    assert (
        ALREADY_REGISTERED_MESSAGE
        in registration_page.get_message()
    )

