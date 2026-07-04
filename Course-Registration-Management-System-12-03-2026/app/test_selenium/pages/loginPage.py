from selenium.webdriver.common.by import By

from app.test_selenium.pages.basePage import BasePage


class LoginPage(BasePage):
    ROLE_COMBOBOX = (By.ID, "roleCombobox")
    ROLE_BUTTON = (By.ID, "roleComboboxButton")
    ROLE_TEXT = (By.ID, "roleComboboxText")
    ROLE_INPUT = (By.ID, "login_role")
    STUDENT_CODE_INPUT = (By.ID, "student_code")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "#loginForm button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".alert-danger h4")
    FORGOT_PASSWORD_LINK = (By.CSS_SELECTOR, "a[href*='forgot-password']")

    def open_page(self):
        self.open_path("/")

    def select_role(self, role):
        self.click(*self.ROLE_BUTTON)
        self.click(By.CSS_SELECTOR, f"[data-value='{role}']")

    def input_student_code(self, student_code):
        self.typing(*self.STUDENT_CODE_INPUT, student_code)

    def input_password(self, password):
        self.typing(*self.PASSWORD_INPUT, password)

    def click_login(self):
        self.click(*self.SUBMIT_BUTTON)

    def login(self, student_code, password, role="student"):
        self.select_role(role)
        self.input_student_code(student_code)
        self.input_password(password)
        self.click_login()
        expected_path = "/admin" if role == "admin" else "/index"
        self.wait_for_url_contains(expected_path)

    def get_error_message(self):
        return self.text(*self.ERROR_MESSAGE)

    def logout(self):
        self.open_path("/logout")

    def click_forgot_password(self):
        self.click(*self.FORGOT_PASSWORD_LINK)

    def student_code_input_is_displayed(self):
        return self.find(*self.STUDENT_CODE_INPUT).is_displayed()

    def password_input_is_displayed(self):
        return self.find(*self.PASSWORD_INPUT).is_displayed()
