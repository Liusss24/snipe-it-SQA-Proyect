from playwright.sync_api import Page


class CheckoutPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self, license_id: int):
        self.page.goto(f"{self.base_url}/licenses/{license_id}/checkout")
        self.page.wait_for_load_state("load")

    def select_user(self, user_name: str):
        """Fills the 'Checkout to' select2 field with the given user name."""
        # Snipe-IT uses Select2 for the assignee field
        field = self.page.locator(".select2-container").first
        field.click()
        search_box = self.page.locator(".select2-search__field")
        search_box.fill(user_name)
        self.page.wait_for_selector(f".select2-results__option:has-text('{user_name}')", timeout=5000)
        self.page.locator(f".select2-results__option:has-text('{user_name}')").first.click()

    def submit(self):
        self.page.locator("button[type=submit]:has-text('Checkout')").click()
        self.page.wait_for_load_state("load")

    def double_click_submit(self):
        btn = self.page.locator("button[type=submit]:has-text('Checkout')")
        btn.dblclick()
        self.page.wait_for_load_state("load")

    def cancel(self):
        cancel = self.page.locator("a:has-text('Cancel'), button:has-text('Cancel')")
        if cancel.count() > 0:
            cancel.first.click()
        else:
            self.page.go_back()
        self.page.wait_for_load_state("load")

    def get_flash_message(self) -> str:
        alert = self.page.locator(".alert").first
        if alert.count() == 0:
            return ""
        return alert.inner_text().strip()

    def get_validation_errors(self) -> list[str]:
        errors = self.page.locator(".invalid-feedback, .help-block.error")
        return [errors.nth(i).inner_text().strip() for i in range(errors.count())]

    def has_no_seats_warning(self) -> bool:
        warning_texts = [
            "no available seats",
            "There are no available seats",
            "no seats",
        ]
        page_text = self.page.content().lower()
        return any(w.lower() in page_text for w in warning_texts)
