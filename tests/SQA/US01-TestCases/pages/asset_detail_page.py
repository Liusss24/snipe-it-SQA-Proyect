from playwright.sync_api import Page


class AssetDetailPage:
    """
    Wraps the Snipe-IT asset detail view (/hardware/{id}).

    Used by:
      CP-HU01-19 – verify action log entry after creation
      CP-HU01-20 – verify Asset Name is displayed escaped (no XSS execution)
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self, asset_id: int):
        self.page.goto(f"{self.base_url}/hardware/{asset_id}")
        self.page.wait_for_load_state("networkidle")

    def get_asset_name_text(self) -> str:
        """
        Returns the displayed value of the Asset Name field on the detail page.
        Snipe-IT renders it inside a <dd> adjacent to the 'Asset Name' label row.
        Falls back to a broader search if the specific selector misses.
        """
        # Primary: look for a definition list row whose label contains 'Asset Name'
        locator = self.page.locator("dl.dl-horizontal dt:has-text('Asset Name') + dd")
        if locator.count() > 0:
            try:
                return locator.first.inner_text().strip()
            except Exception:
                pass

        # Fallback: page-title / h1 that Snipe-IT uses for the asset name
        h1 = self.page.locator("h1.pull-left-xs-only").first
        if h1.count() > 0:
            try:
                return h1.inner_text().strip()
            except Exception:
                pass

        return self.page.title().strip()

    def page_text(self) -> str:
        return self.page.content()

    def is_on_detail_page(self, asset_id: int) -> bool:
        return f"/hardware/{asset_id}" in self.page.url
