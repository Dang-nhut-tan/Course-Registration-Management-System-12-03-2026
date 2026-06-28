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
        rows = self.driver.find_elements(
            *self.FACULTY_ROWS
        )
        for row in rows:
            if faculty_name in row.text:
                row.find_element(
                    *self.EDIT_BUTTON
                ).click()
                return

        raise AssertionError(f"Không tìm thấy khoa: {faculty_name}")

    def set_registration_deadline(self,deadline_value):
        deadline_input = self.driver.find_element(*self.REGISTRATION_DEADLINE_INPUT)
        self.driver.execute_script(
            "arguments[0].value = arguments[1];",
            deadline_input,
            deadline_value,
        )

    def save_faculty(self):
        self.driver.find_element(*self.SUBMIT_BUTTON).click()

    def update_registration_deadline(self,faculty_name,deadline_value):
        self.click_edit_faculty(faculty_name)
        self.set_registration_deadline(deadline_value)
        self.save_faculty()
