import os

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """Common browser operations used by every page object.

    Page objects expose business actions; tests should not need to know Selenium
    locators or call ``driver`` directly.
    """

    BASE_URL = os.getenv("SELENIUM_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    DEFAULT_TIMEOUT = float(os.getenv("SELENIUM_TIMEOUT", "10"))

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)

    def find(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def finds(self, by, value):
        return self.driver.find_elements(by, value)

    def typing(self, by, value, text):
        element = self.find(by, value)
        element.send_keys(text)

    def click(self, by, value):
        self.wait.until(EC.element_to_be_clickable((by, value))).click()

    def open(self, url):
        self.driver.get(url)
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

    def open_path(self, path):
        self.open(f"{self.BASE_URL}/{path.lstrip('/')}")

    def clear_and_type(self, by, value, text):
        element = self.find(by, value)
        element.clear()
        element.send_keys(text)

    def select_index(self, by, value, index):
        field = self.find(by, value)
        selected = self.driver.execute_script(
            """
            const select = arguments[0];
            const rawIndex = arguments[1];
            const index = rawIndex < 0 ? select.options.length + rawIndex : rawIndex;
            if (index < 0 || index >= select.options.length) return false;
            select.selectedIndex = index;
            select.dispatchEvent(new Event('change', {bubbles: true}));
            return true;
            """,
            field,
            index,
        )
        if not selected:
            raise AssertionError(f"Select option index does not exist: {index}")

    def select_value(self, by, value, selected_value):
        field = self.find(by, value)
        selected = self.driver.execute_script(
            """
            const select = arguments[0];
            const value = String(arguments[1]);
            const option = Array.from(select.options).find(item => item.value === value);
            if (!option) return false;
            select.value = value;
            select.dispatchEvent(new Event('change', {bubbles: true}));
            return true;
            """,
            field,
            selected_value,
        )
        if not selected:
            raise AssertionError(f"Select option value does not exist: {selected_value}")

    def select_text_contains(self, by, value, text):
        field = self.find(by, value)
        selected = self.driver.execute_script(
            """
            const select = arguments[0];
            const text = arguments[1];
            const index = Array.from(select.options).findIndex(
                item => item.text.includes(text)
            );
            if (index < 0) return false;
            select.selectedIndex = index;
            select.dispatchEvent(new Event('change', {bubbles: true}));
            return true;
            """,
            field,
            text,
        )
        if not selected:
            raise AssertionError(f"Could not find option containing: {text}")

    def set_value(self, by, value, text):
        element = self.find(by, value)
        self.driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            element,
            text,
        )

    def text(self, by, value):
        return self.wait.until(EC.visibility_of_element_located((by, value))).text.strip()

    def contains_text(self, text):
        return self.wait.until(lambda driver: text in driver.page_source)

    def does_not_contain_text(self, text):
        return self.wait.until(lambda driver: text not in driver.page_source)

    def wait_for_url_contains(self, value):
        return self.wait.until(EC.url_contains(value))
