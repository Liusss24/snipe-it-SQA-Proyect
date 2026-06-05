from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from pages.base_page import BasePage


class CheckoutPage(BasePage):

    CHECKOUT_BUTTON = (By.CSS_SELECTOR, "a.btn-checkout:not(.disabled)")
    USER_CONTAINER  = (By.ID, "select2-assigned_user_select-container")
    USER_SEARCH     = (By.CSS_SELECTOR, ".select2-search__field")
    SUBMIT_BUTTON   = (By.ID, "submit_button")
    SUCCESS_ALERT   = (By.CSS_SELECTOR, ".alert-success")

    def checkout_first_available(self):
        """Checks out the first RTD asset to the first user found. Returns True on success."""
        self.go_to("/hardware?status_type=RTD")
        try:
            self.js_click(*self.CHECKOUT_BUTTON)
        except TimeoutException:
            return False

        try:
            self.wait_for_clickable(*self.USER_CONTAINER).click()
            search = self.wait_for_clickable(*self.USER_SEARCH)
            search.send_keys("a")
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".select2-results__option:not(.loading-results)")
            ))
            for _ in range(5):
                try:
                    opts = self.driver.find_elements(
                        By.CSS_SELECTOR, ".select2-results__option:not(.loading-results)"
                    )
                    if opts:
                        opts[0].click()
                        break
                except StaleElementReferenceException:
                    continue
        except Exception:
            return False

        self.wait_for_clickable(*self.SUBMIT_BUTTON).click()
        try:
            self.wait.until(EC.presence_of_element_located(self.SUCCESS_ALERT))
            return True
        except Exception:
            return False
