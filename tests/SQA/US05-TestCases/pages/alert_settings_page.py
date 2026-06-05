"""
Page Object – Admin > Settings > Alerts

Used by CP-HU05-11 and CP-HU05-12 to verify the UI state of the alerts
configuration page in Snipe-IT v8.
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
        if locator.count() == 0:
            return ""
        return locator.input_value()

    def get_alert_interval(self) -> str:
        """Returns the current value of the alert interval (days threshold) field."""
        locator = self.page.locator("input[name='alert_interval']")
        if locator.count() == 0:
            return ""
        return locator.input_value()

    def page_text(self) -> str:
        return self.page.locator("body").inner_text(timeout=5000)


class LicenseDetailPage:
    """
    Wraps the Snipe-IT license detail page (/licenses/{id}).

    Used by CP-HU05-14 (manual) to verify that an expiring license
    shows a visible warning banner.
    """

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
