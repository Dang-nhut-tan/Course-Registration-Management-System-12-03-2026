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