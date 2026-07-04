import re
from urllib.parse import urlencode

from selenium.webdriver.common.by import By

from app.test_selenium.pages.basePage import BasePage


class StudentRegistrationPage(BasePage):
    PATH = "index"
    MESSAGE = (
        By.CSS_SELECTOR,
        "[data-registration-page] > div.mb-4.rounded-lg.px-4.py-3",
    )
    REGISTERED_COUNT = (By.CSS_SELECTOR, ".registration-panel h3 strong")
    REGISTERED_CREDITS = (By.CSS_SELECTOR, "p.mb-2 strong")
    OPEN_SECTION_ROWS = (By.CSS_SELECTOR, ".registration-table-wrap tbody tr")
    REGISTERED_ROWS = (By.CSS_SELECTOR, ".registration-panel tbody tr")
    REGISTER_BUTTON = (By.CSS_SELECTOR, ".js-register-course button")
    CANCEL_BUTTON = (By.CSS_SELECTOR, ".js-cancel-course button")

    def open_page(self, **params):
        query = f"?{urlencode(params)}" if params else ""
        self.open_path(f"{self.PATH}{query}")

    def get_message(self):
        return self.text(*self.MESSAGE)

    def get_registered_count(self):
        text = self.find(*self.REGISTERED_COUNT).text
        match = re.search(r"\d+", text)
        return int(match.group(0)) if match else 0

    def get_registered_credits(self):
        return int(self.text(*self.REGISTERED_CREDITS))

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

    def register_course_from_result(self, result_number):
        rows = self.finds(*self.OPEN_SECTION_ROWS)
        if result_number < 1 or result_number > len(rows):
            raise AssertionError(f"Registration result {result_number} does not exist")
        rows[result_number - 1].find_element(*self.REGISTER_BUTTON).click()

    def has_open_course(self, course_name):
        return any(course_name in row.text for row in self.finds(*self.OPEN_SECTION_ROWS))
