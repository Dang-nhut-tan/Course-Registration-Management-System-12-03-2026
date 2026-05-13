from selenium.webdriver.common.by import By

from app.test.pages.loginPage import LoginPage
from app.test.test_base import driver, test_app
import time


def test_open_login_page(driver):
    login = LoginPage(driver=driver)
    login.open_page()

    assert driver.find_element(By.ID, "student_code").is_displayed()
    assert driver.find_element(By.ID, "password").is_displayed()



def test_login_fail(driver):
    login = LoginPage(driver=driver)
    login.open_page()

    login.login("wrong-user", "wrong-password")
    time.sleep(1)

    error = driver.find_element(By.CSS_SELECTOR, ".alert-danger h4")
    assert error.text != ""



def test_login_success(driver):
    login = LoginPage(driver=driver)
    login.open_page()

    login.login("2354050113", "123456")
    time.sleep(1)

    assert "/index" in driver.current_url



def test_login_admin_success(driver):
    login = LoginPage(driver=driver)
    login.open_page()

    login.login("admin", "admin123", role="admin")
    time.sleep(1)

    assert "/course/" in driver.current_url

