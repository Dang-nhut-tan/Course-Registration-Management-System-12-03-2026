import re
from urllib.parse import urlencode

from selenium.webdriver.common.by import By

from app.test.pages.basePage import BasePage


class StudentRegistrationPage(BasePage):
    BASE_URL = "http://127.0.0.1:5000/index"
    MESSAGE = (By.CSS_SELECTOR, ".p-6 > div.mb-4")
    REGISTERED_COUNT = (By.CSS_SELECTOR, ".registration-panel h3 strong")
    OPEN_SECTION_ROWS = (By.CSS_SELECTOR, ".registration-table-wrap tbody tr")
    REGISTERED_ROWS = (By.CSS_SELECTOR, ".registration-panel tbody tr")
    REGISTER_BUTTON = (By.CSS_SELECTOR, "form[action$='register-course'] button")
    CANCEL_BUTTON = (By.CSS_SELECTOR, "form[action$='cancel-course'] button")

    def open_page(self, **params):
        query = f"?{urlencode(params)}" if params else ""
        self.open(f"{self.BASE_URL}{query}")

    def get_message(self):
        return self.find(*self.MESSAGE).text.strip()

    def get_registered_count(self):
        text = self.find(*self.REGISTERED_COUNT).text
        match = re.search(r"\d+", text)
        return int(match.group(0)) if match else 0

    def _row_containing(self, rows_locator, text):
        for row in self.finds(*rows_locator):
            if text in row.text:
                return row
        raise AssertionError(f"Could not find row containing: {text}")

    def register_course(self, course_name):
        row = self._row_containing(self.OPEN_SECTION_ROWS, course_name)
        row.find_element(*self.REGISTER_BUTTON).click()

    def cancel_course(self, course_name):
        row = self._row_containing(self.REGISTERED_ROWS, course_name)
        row.find_element(*self.CANCEL_BUTTON).click()
