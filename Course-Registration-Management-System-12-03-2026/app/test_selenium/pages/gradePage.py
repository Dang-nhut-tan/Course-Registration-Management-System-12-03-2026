import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from app.test_selenium.pages.basePage import BasePage


class GradePage(BasePage):
    URL = "http://127.0.0.1:5000/admin/grade/"

    CREATE_BUTTON = (By.XPATH, "//a[contains(@href,'/admin/grade/new')]")
    ENROLLMENT_SELECT2 = (By.ID, "s2id_enrollment")
    SELECT2_INPUT = (By.CSS_SELECTOR, ".select2-input")
    SELECT2_RESULT = (By.CSS_SELECTOR, ".select2-result-label")
    MIDTERM_INPUT = (By.NAME, "midterm_score")
    SAVE_BUTTON = (By.CSS_SELECTOR, "input[type='submit']")

    def open_list(self):
        self.open(self.URL)

    def wait_clickable(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_visible(self, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def click_create(self):
        create_button = self.wait_clickable(self.CREATE_BUTTON, timeout=15)
        self.driver.execute_script("arguments[0].click();", create_button)

    def select_enrollment(self, student_code):
        self.wait_clickable(self.ENROLLMENT_SELECT2).click()

        search_input = self.wait_visible(self.SELECT2_INPUT)
        search_input.clear()
        search_input.send_keys(student_code)
        time.sleep(2)

        self.wait_visible(self.SELECT2_RESULT)
        search_input.send_keys(Keys.ARROW_DOWN)
        search_input.send_keys(Keys.ENTER)

    def input_midterm_score(self, score):
        score_input = self.wait_visible(self.MIDTERM_INPUT)
        score_input.clear()
        score_input.send_keys(score)

    def click_save(self):
        save_button = self.wait_clickable(self.SAVE_BUTTON)
        self.driver.execute_script("arguments[0].click();", save_button)

    def create_midterm_score(self, student_code, score):
        self.click_create()
        time.sleep(2)
        self.select_enrollment(student_code)
        time.sleep(1)
        self.input_midterm_score(score)
        time.sleep(1)
        self.click_save()
        time.sleep(2)
