from playwright.sync_api import Page


class LicenseDetailPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self, license_id: int):
        self.page.goto(f"{self.base_url}/licenses/{license_id}")
        self.page.wait_for_load_state("load")

    def get_available_seats(self) -> str:
        """Returns the text of the 'Remaining Seats' info row."""
        label = self.page.locator("text=Remaining Seats").first
        if label.count() == 0:
            label = self.page.locator("text=Available Seats").first
        return label.locator("xpath=following-sibling::*[1]").inner_text().strip()

    def get_checked_out_count(self) -> str:
        label = self.page.locator("text=Checked Out").first
        return label.locator("xpath=following-sibling::*[1]").inner_text().strip()

    def checkout_button_is_visible(self) -> bool:
        btn = self.page.locator("a:has-text('Checkout'), button:has-text('Checkout')")
        return btn.count() > 0 and btn.first.is_visible()

    def checkout_button_is_enabled(self) -> bool:
        btn = self.page.locator("a:has-text('Checkout'), button:has-text('Checkout')")
        if btn.count() == 0:
            return False
        return btn.first.is_enabled()

    def click_checkout(self):
        self.page.locator("a:has-text('Checkout'), button:has-text('Checkout')").first.click()
        self.page.wait_for_load_state("load")

    def get_flash_message(self) -> str:
        alert = self.page.locator(".alert").first
        if alert.count() == 0:
            return ""
        return alert.inner_text().strip()
