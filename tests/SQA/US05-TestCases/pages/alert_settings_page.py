"""
Page Object – Admin > Settings > Alerts (/settings/alerts)

Used by CP-HU05-14 (manual) to verify the UI state of the alert
configuration page in Snipe-IT v8.

Note: CP-HU05-11 and CP-HU05-12 verify alerts via the artisan command
output (backend), not the UI. This page object is provided for manual
exploratory testing and future UI-level assertions.
"""
from playwright.sync_api import Page


class AlertSettingsPage:
    """Wraps Admin > Settings > Alerts (/settings/alerts)."""

    URL_PATH = "/settings/alerts"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}{self.URL_PATH}")
        self.page.wait_for_load_state("networkidle")

    def get_alert_email(self) -> str:
        """Returns the current value of the alert email field."""
        locator = self.page.locator("input[name='alert_email']")
        return locator.input_value() if locator.count() > 0 else ""

    def get_alert_interval(self) -> str:
        """Returns the current threshold value (days) for expiry alerts."""
        locator = self.page.locator("input[name='alert_interval']")
        return locator.input_value() if locator.count() > 0 else ""

    def page_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=5000)
