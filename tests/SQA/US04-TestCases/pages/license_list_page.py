from playwright.sync_api import Page


class LicenseListPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}/licenses")
        self.page.wait_for_load_state("load")

    def get_available_seats_for(self, license_name: str) -> str | None:
        """Returns the visible 'Available' seat count from the list row."""
        row = self.page.locator(f"tr:has-text('{license_name}')")
        if row.count() == 0:
            return None
        # Column index 5 = "Remaining Seats" in default Snipe-IT list
        cells = row.locator("td")
        for i in range(cells.count()):
            text = cells.nth(i).inner_text().strip()
            if text.isdigit():
                return text
        return None

    def open_license(self, license_name: str):
        self.page.locator(f"a:has-text('{license_name}')").first.click()
        self.page.wait_for_load_state("load")
