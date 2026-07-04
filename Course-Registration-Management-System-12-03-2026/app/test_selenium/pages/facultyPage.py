from selenium.webdriver.common.by import By

from app.test_selenium.pages.adminBasePage import AdminBasePage


class FacultyPage(AdminBasePage):

    LIST_URL = "faculty/"

    FACULTY_ROWS = (By.CSS_SELECTOR, "table tbody tr")
    EDIT_BUTTON = (By.CSS_SELECTOR, "a[title='Edit Record']")
    REGISTRATION_DEADLINE_INPUT = (By.ID, "registration_deadline")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "input[type='submit']")

    def open_list(self):
        self.open_list_path(self.LIST_URL)

    def click_edit_faculty(self,faculty_name):
        self.open_list()
        self.click_edit_for_row_containing(faculty_name)

    def set_registration_deadline(self,deadline_value):
        self.set_value(*self.REGISTRATION_DEADLINE_INPUT, deadline_value)

    def save_faculty(self):
        self.submit()

    def update_registration_deadline(self,faculty_name,deadline_value):
        self.click_edit_faculty(faculty_name)
        self.set_registration_deadline(deadline_value)
        self.save_faculty()
