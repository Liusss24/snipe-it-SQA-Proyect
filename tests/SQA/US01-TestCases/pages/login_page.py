from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}/login")

    def login(self, username: str, password: str):
        self.page.fill("input[name='username']", username)
        self.page.fill("input[name='password']", password)
        self.page.click("button[type='submit']")
        self.page.wait_for_load_state("load")

    def is_on_login_page(self) -> bool:
        return "/login" in self.page.url
