from playwright.sync_api import Page


class LicenseListPage:
    """
    Wraps the Snipe-IT license list page (/licenses).

    The list table is rendered by Bootstrap Table + AJAX; wait_for_load_state
    "networkidle" ensures the data has loaded before assertions.
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}/licenses")
        self.page.wait_for_load_state("networkidle")

    def find_row(self, license_name: str):
        """Returns the table row locator for a license, or None."""
        row = self.page.locator(f"tr:has-text('{license_name}')")
        return row if row.count() > 0 else None

    def open_license(self, license_name: str):
        self.page.locator(f"a:has-text('{license_name}')").first.click()
        self.page.wait_for_load_state("networkidle")
