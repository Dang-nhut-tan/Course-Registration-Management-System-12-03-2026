from selenium.webdriver.common.by import By

from app.test_selenium.pages.adminBasePage import AdminBasePage


class TeacherCoursePage(AdminBasePage):
    LIST_URL = "teachercourse/"
    CREATE_URL = "teachercourse/new/"

    TEACHER_SELECT = (By.ID, "teacher")
    COURSE_SELECT = (By.ID, "course")

    def open_list(self):
        self.open_list_path(self.LIST_URL)

    def open_create(self):
        self.open_admin_path(self.CREATE_URL)

    def create_teacher_course(
        self,
        teacher_index=-1,
        course_index=1,
        teacher_name=None,
        course_name=None,
    ):
        self.open_create()
        if teacher_name:
            self.select_text_contains(*self.TEACHER_SELECT, teacher_name)
        else:
            self.select_index(*self.TEACHER_SELECT, teacher_index)

        if course_name:
            self.select_text_contains(*self.COURSE_SELECT, course_name)
        else:
            self.select_index(*self.COURSE_SELECT, course_index)

        self.submit()

    def edit_teacher_course(self, teacher_name, course_index=2):
        self.open_list()
        self.click_edit_for_row_containing(teacher_name)
        self.select_index(*self.COURSE_SELECT, course_index)
        self.submit()

    def delete_teacher_course(self, teacher_name):
        self.open_list()
        self.delete_row_containing(teacher_name)
