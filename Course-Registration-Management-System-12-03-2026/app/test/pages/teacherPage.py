from selenium.webdriver.common.by import By

from app.test.pages.adminBasePage import AdminBasePage


class TeacherPage(AdminBasePage):
    LIST_URL = "teacher/"
    CREATE_URL = "teacher/new/"

    NAME_INPUT = (By.ID, "name")

    def open_list(self):
        self.open_list_path(self.LIST_URL)

    def open_create(self):
        self.open_admin_path(self.CREATE_URL)

    def create_teacher(self, name):
        self.open_create()
        self.typing(*self.NAME_INPUT, name)
        self.submit()

    def edit_teacher_name(self, current_name, new_name):
        self.open_list()
        self.click_edit_for_row_containing(current_name)
        self.clear_and_type(*self.NAME_INPUT, new_name)
        self.submit()

    def delete_teacher(self, name):
        self.open_list()
        self.delete_row_containing(name)

