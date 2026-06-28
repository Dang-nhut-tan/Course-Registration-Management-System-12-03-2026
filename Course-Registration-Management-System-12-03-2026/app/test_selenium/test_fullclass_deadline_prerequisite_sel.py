import time
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from app.test_selenium.pages.classSectionPage import ClassSectionPage
from app.test_selenium.pages.loginPage import LoginPage
from app.test_selenium.pages.studentRegistrationPage import StudentRegistrationPage
from app.test_selenium.pages.facultyPage import FacultyPage

from app.test.test_base import driver

FULL_CLASS_MESSAGE = "Lớp học phần đã hết chỗ."
PREREQUISITE_MESSAGE = "Thiếu tiên quyết: Cơ sở dữ liệu"


FACULTY_LIST_URL = "http://127.0.0.1:5000/admin/faculty/"
COURSE_NAME = "Cấu trúc dữ liệu và giải thuật"
REGISTRATION_DEADLINE_INPUT = (By.ID,"registration_deadline")
SUBMIT_BUTTON = (By.CSS_SELECTOR,"input[type='submit']")
FACULTY_ROWS = (By.CSS_SELECTOR,"table tbody tr")
EDIT_BUTTON = (By.CSS_SELECTOR,"a[title='Edit Record']")

REGISTRATION_ROWS = (By.CSS_SELECTOR,".registration-table-wrap tbody tr")


def student_login(driver, student_code):
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(
        student_code,
        "123456",
    )
    time.sleep(1)


def test_student_cannot_register_full_class(driver):
    course_name = "Tư tưởng Hồ Chí Minh"

    class_section_page = ClassSectionPage(driver)

    class_section_page.admin_login()

    class_section_page.edit_max_students(course_name,"1")
    time.sleep(2)
    student_login(driver,"2354050114")
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(course_query=course_name)
    time.sleep(2)
    registration_page.register_course(course_name)
    time.sleep(2)
    driver.get("http://127.0.0.1:5000/logout")
    time.sleep(1)
    student_login(driver,"2354050115")
    registration_page.open_page(course_query=course_name)
    time.sleep(2)
    registration_page.register_course(course_name)
    time.sleep(2)

    assert (
        FULL_CLASS_MESSAGE
        in registration_page.get_message()
    )

def test_student_cannot_register_without_prerequisite(driver):
    course_name = "Phân tích thiết kế hệ thống"
    student_login(driver,"2354050113")
    registration_page = StudentRegistrationPage(driver)
    registration_page.open_page(course_query=course_name)
    time.sleep(2)
    registration_page.register_course(course_name)
    time.sleep(2)
    assert (PREREQUISITE_MESSAGE
            in registration_page.get_message()
    )


def test_student_cannot_register_after_deadline(driver):
    faculty_page = FacultyPage(driver)
    faculty_page.admin_login()

    # SET DEADLINE = YESTERDAY
    yesterday = (
            datetime.now()
            - timedelta(days=1)
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    faculty_page = FacultyPage(driver)

    faculty_page.update_registration_deadline(
        faculty_name="CNTT",
        deadline_value=yesterday,
    )

    time.sleep(2)

    # LOGIN STUDENT
    student_login(driver,"2354050113")

    # OPEN REGISTRATION PAGE
    registration_page = StudentRegistrationPage(driver)

    registration_page.open_page(course_query=COURSE_NAME)

    time.sleep(2)

    # ASSERT COURSE NOT DISPLAYED
    rows = driver.find_elements(*REGISTRATION_ROWS)

    found = False

    for row in rows:
        if COURSE_NAME in row.text:
            found = True
            break

    assert not found
