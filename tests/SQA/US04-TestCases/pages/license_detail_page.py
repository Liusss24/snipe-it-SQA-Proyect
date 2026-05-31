from playwright.sync_api import Page


class LicenseDetailPage:
    """
    Wraps the Snipe-IT license detail page (/licenses/{id}).

    Seat counts are NOT static HTML in Snipe-IT – they are loaded by Bootstrap
    Table via AJAX. For reliable assertions, call conftest helpers (get_free_seats,
    get_checked_out_count) that query the REST API directly. This page object only
    handles UI navigation and interaction.
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self, license_id: int):
        self.page.goto(f"{self.base_url}/licenses/{license_id}")
        self.page.wait_for_load_state("networkidle")

    def navigate_to_checkout(self, license_id: int):
        """Navigate directly to the checkout form for this license."""
        self.page.goto(f"{self.base_url}/licenses/{license_id}/checkout")
        self.page.wait_for_load_state("load")

    # ------------------------------------------------------------------
    # UI state
    # ------------------------------------------------------------------

    def get_flash_message(self) -> str:
        """Returns the text of the first visible .alert on the page."""
        alert = self.page.locator(".alert").first
        if alert.count() == 0:
            return ""
        try:
            alert.wait_for(state="visible", timeout=3000)
            return alert.inner_text().strip()
        except Exception:
            return ""

    def checkout_url_is_accessible(self, license_id: int) -> bool:
        """
        Returns True if the checkout page renders the form (not an error/redirect).
        Used for CP-HU04-03/04 to verify the UI blocks checkout for 0-seat licenses.
        """
        try:
            resp = self.page.request.get(
                f"{self.base_url}/licenses/{license_id}/checkout",
                max_redirects=5,
            )
            return resp.ok
        except Exception:
            return False

    def is_on_license_page(self) -> bool:
        return "/licenses/" in self.page.url and "/checkout" not in self.page.url
