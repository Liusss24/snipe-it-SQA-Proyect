from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class BasePage:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def go_to(self, path=""):
        self.driver.get(f"{self.base_url}{path}")

    def wait_for_element(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def wait_for_clickable(self, by, value):
        return self.wait.until(EC.element_to_be_clickable((by, value)))

    def js_click(self, by, value):
        """Click via JavaScript to bypass fixed-columns overlay interception."""
        el = self.wait_for_clickable(by, value)
        self.driver.execute_script("arguments[0].click()", el)

    def wait_for_url_contains(self, text):
        self.wait.until(EC.url_contains(text))

    def get_alert_text(self):
        alert = self.wait_for_element(By.CSS_SELECTOR, ".alert")
        return alert.text

    def is_alert_success(self):
        try:
            self.wait_for_element(By.CSS_SELECTOR, ".alert-success")
            return True
        except Exception:
            return False
