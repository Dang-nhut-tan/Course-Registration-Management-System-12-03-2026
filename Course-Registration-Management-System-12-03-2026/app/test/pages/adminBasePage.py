from selenium.webdriver.common.by import By

from app.test.pages.basePage import BasePage


class AdminBasePage(BasePage):
    BASE_URL = "http://127.0.0.1:5000/admin"
    LIST_PAGE_SIZE = 1000
    MAX_LIST_PAGES = 100
    CREATE_LINK = (By.LINK_TEXT, "Create")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "input[type='submit']")
    CREATED_MESSAGE = "Record was successfully created."
    SAVED_MESSAGE = "Record was successfully saved."
    DELETED_MESSAGE = "Record was successfully deleted."
    SUCCESS_MESSAGE = CREATED_MESSAGE
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")
    EDIT_LINK = (By.CSS_SELECTOR, "a[title='Edit Record']")
    DELETE_BUTTON = (By.CSS_SELECTOR, "form[action$='/delete/'] button")

    def open_admin_path(self, path):
        self.open(f"{self.BASE_URL}/{path.lstrip('/')}")

    def open_list_path(self, path):
        separator = "&" if "?" in path else "?"
        self.open_admin_path(f"{path}{separator}page_size={self.LIST_PAGE_SIZE}")

    def open_list_page(self, page):
        list_url = getattr(self, "LIST_URL", None)
        if not list_url:
            raise AssertionError("Page object must define LIST_URL to scan admin list pages.")
        self.open_admin_path(f"{list_url}?page={page}")

    def submit(self):
        self.click(*self.SUBMIT_BUTTON)

    def has_success_message(self):
        return self.SUCCESS_MESSAGE in self.driver.page_source

    def has_message(self, message):
        return message in self.driver.page_source

    def has_created_message(self):
        return self.has_message(self.CREATED_MESSAGE)

    def has_saved_message(self):
        return self.has_message(self.SAVED_MESSAGE)

    def has_deleted_message(self):
        return self.has_message(self.DELETED_MESSAGE)

    def row_containing(self, text):
        for row in self.finds(*self.TABLE_ROWS):
            if text in row.text:
                return row

        if hasattr(self, "LIST_URL"):
            for page in range(self.MAX_LIST_PAGES):
                self.open_list_page(page)
                rows = self.finds(*self.TABLE_ROWS)
                for row in rows:
                    if text in row.text:
                        return row
                if len(rows) == 1 and "There are no items in the table." in rows[0].text:
                    break

        raise AssertionError(f"Could not find admin row containing: {text}")

    def click_edit_for_row_containing(self, text):
        row = self.row_containing(text)
        row.find_element(*self.EDIT_LINK).click()

    def delete_row_containing(self, text):
        row = self.row_containing(text)
        row.find_element(*self.DELETE_BUTTON).click()
        self.driver.switch_to.alert.accept()
