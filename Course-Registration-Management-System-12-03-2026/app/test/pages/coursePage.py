from selenium.webdriver.common.by import By

from app.test.pages.adminBasePage import AdminBasePage


class CoursePage(AdminBasePage):
    LIST_URL = "course/"
    CREATE_URL = "course/new/"

    FACULTY_SELECT = (By.ID, "faculty")
    NAME_INPUT = (By.ID, "name")
    CREDITS_INPUT = (By.ID, "credits")

    def open_list(self):
        self.open_list_path(self.LIST_URL)

    def open_create(self):
        self.open_admin_path(self.CREATE_URL)

    def click_create(self):
        self.click(*self.CREATE_LINK)

    def create_course(self, name, credits="3", faculty_index=1):
        self.open_create()
        self.fill_course_form(name, credits, faculty_index)
        self.submit()

    def fill_course_form(self, name, credits="3", faculty_index=1):
        self.select_index(*self.FACULTY_SELECT, faculty_index)
        self.typing(*self.NAME_INPUT, name)
        self.clear_and_type(*self.CREDITS_INPUT, credits)

    def edit_course_name(self, current_name, new_name):
        self.open_list()
        self.click_edit_for_row_containing(current_name)
        self.clear_and_type(*self.NAME_INPUT, new_name)
        self.submit()

    def delete_course(self, name):
        self.open_list()
        self.delete_row_containing(name)
