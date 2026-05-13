class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def find(self, by, value):
        return self.driver.find_element(by, value)

    def finds(self, by, value):
        return self.driver.find_elements(by, value)

    def typing(self, by, value, text):
        element = self.find(by, value)
        element.send_keys(text)

    def click(self, by, value):
        self.find(by, value).click()

    def open(self, url):
        self.driver.get(url)

    def clear_and_type(self, by, value, text):
        element = self.find(by, value)
        element.clear()
        element.send_keys(text)

    def select_index(self, by, value, index):
        field = self.find(by, value)
        self.driver.execute_script(
            """
            const select = arguments[0];
            const rawIndex = arguments[1];
            const index = rawIndex < 0 ? select.options.length + rawIndex : rawIndex;
            select.selectedIndex = index;
            select.dispatchEvent(new Event('change'));
            """,
            field,
            index,
        )

    def select_value(self, by, value, selected_value):
        field = self.find(by, value)
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; "
            "arguments[0].dispatchEvent(new Event('change'));",
            field,
            selected_value,
        )

    def select_text_contains(self, by, value, text):
        field = self.find(by, value)
        self.driver.execute_script(
            """
            const select = arguments[0];
            const text = arguments[1];
            for (let i = 0; i < select.options.length; i++) {
                if (select.options[i].text.includes(text)) {
                    select.selectedIndex = i;
                    select.dispatchEvent(new Event('change'));
                    return;
                }
            }
            """,
            field,
            text,
        )

    def set_value(self, by, value, text):
        element = self.find(by, value)
        self.driver.execute_script("arguments[0].value = arguments[1];", element, text)
