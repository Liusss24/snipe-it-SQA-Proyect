from playwright.sync_api import Page


class AssetListPage:
    """
    Wraps the Snipe-IT asset list page (/hardware).

    The table is rendered by Bootstrap Table + AJAX; use the search box to
    filter and 'networkidle' to wait for data.
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}/hardware")
        self.page.wait_for_load_state("networkidle")

    def search(self, term: str):
        box = self.page.locator("input.search-input, input[type='search']").first
        box.fill(term)
        box.press("Enter")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def find_row(self, text: str):
        row = self.page.locator(f"tr:has-text('{text}')")
        return row if row.count() > 0 else None

    def row_contains(self, row_text: str, *expected: str) -> bool:
        row = self.find_row(row_text)
        if row is None:
            return False
        content = row.first.inner_text()
        return all(e in content for e in expected)
