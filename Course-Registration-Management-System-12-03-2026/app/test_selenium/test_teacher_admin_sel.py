import time
from app.test_selenium.pages.teacherPage import TeacherPage
from app.test.test_base import driver

DELETE_TEACHER_FAILED_MESSAGE = "Không thể xóa giáo viên vì giáo viên này đang được gán cho lớp học phần."

def test_admin_create_teacher(driver):
    teacher_name = f"Selenium Teacher {int(time.time())}"
    edited_teacher_name = f"{teacher_name} Edited"

    teacher_page = TeacherPage(driver)
    teacher_page.admin_login()


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

def test_admin_cannot_delete_teacher_has_classsection(driver):
    teacher_name = "Thầy B"

    teacher_page = TeacherPage(driver)
    teacher_page.admin_login()

    # OPEN TEACHER PAGE
    teacher_page = TeacherPage(driver)
    teacher_page.open_list()
    time.sleep(2)

    # DELETE TEACHER
    teacher_page.delete_teacher(teacher_name)
    time.sleep(2)

    # ASSERT DELETE FAILED MESSAGE
    assert (
        DELETE_TEACHER_FAILED_MESSAGE
        in driver.page_source
    )

    # ASSERT TEACHER STILL EXISTS
    assert (
        teacher_name
        in driver.page_source
    )
