from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class LoginPage(BasePage):

    USERNAME_INPUT = (By.NAME, "username")
    PASSWORD_INPUT = (By.NAME, "password")
    SUBMIT_BUTTON  = (By.CSS_SELECTOR, "button[type='submit']")

    def load(self):
        self.go_to("/login")

    def login(self, username, password):
        self.wait_for_clickable(*self.USERNAME_INPUT).clear()
        self.driver.find_element(*self.USERNAME_INPUT).send_keys(username)
        self.driver.find_element(*self.PASSWORD_INPUT).send_keys(password)
        self.driver.find_element(*self.SUBMIT_BUTTON).click()
        # Esperar a que la URL ya no sea la de login (Snipe-IT puede redirigir a / o /dashboard)
        self.wait.until(lambda d: "/login" not in d.current_url)
