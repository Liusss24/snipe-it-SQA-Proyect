from playwright.sync_api import Page


class UserProfilePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self, user_id: int):
        self.page.goto(f"{self.base_url}/users/{user_id}")
        self.page.wait_for_load_state("load")

    def get_license_names(self) -> list[str]:
        """Returns the list of license names visible in the Licenses section."""
        # Snipe-IT shows assigned licenses in a tab/section on the user detail page
        licenses_section = self.page.locator("#licenses, [data-tab='licenses'], section:has-text('Licenses')")
        if licenses_section.count() == 0:
            # Fallback: look for the Licenses heading and sibling table
            licenses_section = self.page.locator("h3:has-text('Licenses'), h4:has-text('Licenses')")

        rows = self.page.locator("table:near(:text('Licenses')) tr td:first-child, #licenses td:first-child")
        return [rows.nth(i).inner_text().strip() for i in range(rows.count())]

    def license_is_listed(self, license_name: str) -> bool:
        return license_name in self.get_license_names()
