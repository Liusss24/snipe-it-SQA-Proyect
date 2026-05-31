from playwright.sync_api import Page


class UserProfilePage:
    """
    Wraps the Snipe-IT user detail page (/users/{id}).

    License assignment verification is done via the REST API
    (GET /api/v1/users/{id}/licenses) because the licenses tab is loaded by
    Bootstrap Table via AJAX. Use conftest.user_has_license() for that.
    This class handles UI navigation only.
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self, user_id: int):
        self.page.goto(f"{self.base_url}/users/{user_id}")
        self.page.wait_for_load_state("networkidle")
