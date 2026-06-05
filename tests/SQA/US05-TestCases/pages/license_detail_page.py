"""
Page Object – License detail page (/licenses/{id})

Used by CP-HU05-14 (manual) to verify that an expiring license
shows a visible warning banner in Snipe-IT v8.
"""
from playwright.sync_api import Page


class LicenseDetailPage:
    """Wraps the Snipe-IT license detail page (/licenses/{id})."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self, license_id: int):
        self.page.goto(f"{self.base_url}/licenses/{license_id}")
        self.page.wait_for_load_state("networkidle")

    def has_expiry_warning(self) -> bool:
        """True if a Bootstrap warning alert is visible on the page."""
        warning = self.page.locator(".alert-warning, .callout-warning")
        return warning.count() > 0 and warning.first.is_visible()

    def page_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=5000)
