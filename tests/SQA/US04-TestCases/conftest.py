import os
import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import Playwright, Page, BrowserContext

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

BASE_URL = os.getenv("SNIPEIT_BASE_URL", "http://localhost:8000")
ADMIN_USERNAME = os.getenv("SNIPEIT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("SNIPEIT_ADMIN_PASSWORD", "password")
API_TOKEN = os.getenv("SNIPEIT_API_TOKEN", "")
NOPERM_USERNAME = os.getenv("SNIPEIT_NOPERM_USERNAME", "viewer")
NOPERM_PASSWORD = os.getenv("SNIPEIT_NOPERM_PASSWORD", "password")


# ---------------------------------------------------------------------------
# Browser / page fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def context(playwright: Playwright) -> BrowserContext:
    browser = playwright.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    yield ctx
    ctx.close()
    browser.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    return context.new_page()


@pytest.fixture(scope="function")
def auth_page(context: BrowserContext) -> Page:
    """Page already logged in as admin."""
    p = context.new_page()
    p.goto(f"{BASE_URL}/login")
    p.fill("#username", ADMIN_USERNAME)
    p.fill("#password", ADMIN_PASSWORD)
    p.click("button[type=submit]")
    p.wait_for_url(f"{BASE_URL}/**", wait_until="load")
    return p


@pytest.fixture(scope="function")
def noperm_page(context: BrowserContext) -> Page:
    """Page logged in as a user without manage-licenses permission."""
    p = context.new_page()
    p.goto(f"{BASE_URL}/login")
    p.fill("#username", NOPERM_USERNAME)
    p.fill("#password", NOPERM_PASSWORD)
    p.click("button[type=submit]")
    p.wait_for_url(f"{BASE_URL}/**", wait_until="load")
    return p


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _api(method: str, endpoint: str, data: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    url = f"{BASE_URL}/api/v1{endpoint}"
    resp = requests.request(method, url, json=data, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _first_category_id() -> int:
    """Returns the id of the first existing license category."""
    result = _api("GET", "/categories?limit=1&category_type=license")
    rows = result.get("rows", [])
    if not rows:
        raise RuntimeError(
            "No license category found. Create at least one in Snipe-IT before running tests."
        )
    return rows[0]["id"]


# ---------------------------------------------------------------------------
# Test-data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def license_2_seats():
    """LIC-HU04-01 equivalent: license with 2 available seats."""
    cat_id = _first_category_id()
    data = _api("POST", "/licenses", {
        "name": "LIC-HU04-01",
        "seats": 2,
        "category_id": cat_id,
    })
    lic = data.get("payload", {})
    yield lic
    if lic.get("id"):
        _api("DELETE", f"/licenses/{lic['id']}")


@pytest.fixture
def license_1_seat():
    """LIC-HU04-02 equivalent: license with 1 available seat."""
    cat_id = _first_category_id()
    data = _api("POST", "/licenses", {
        "name": "LIC-HU04-02",
        "seats": 1,
        "category_id": cat_id,
    })
    lic = data.get("payload", {})
    yield lic
    if lic.get("id"):
        _api("DELETE", f"/licenses/{lic['id']}")


@pytest.fixture
def license_0_seats():
    """LIC-HU04-03 equivalent: license with 0 available seats (fully checked out)."""
    cat_id = _first_category_id()
    data = _api("POST", "/licenses", {
        "name": "LIC-HU04-03",
        "seats": 1,
        "category_id": cat_id,
    })
    lic = data.get("payload", {})
    lic_id = lic.get("id")

    # Create a temporary user and check out the only seat via API
    user_data = _api("POST", "/users", {
        "first_name": "Temp",
        "last_name": "Seat",
        "username": f"temp.seat.{lic_id}",
        "email": f"temp.seat.{lic_id}@test.local",
        "password": "TempPass123!",
        "activated": True,
    })
    tmp_user = user_data.get("payload", {})

    if lic_id and tmp_user.get("id"):
        _api("POST", f"/licenses/{lic_id}/checkout", {
            "checkout_to_type": "user",
            "assigned_to": tmp_user["id"],
        })

    yield lic

    if tmp_user.get("id"):
        _api("DELETE", f"/users/{tmp_user['id']}")
    if lic_id:
        _api("DELETE", f"/licenses/{lic_id}")


@pytest.fixture
def user_juan():
    """Creates the test user Juan Pérez."""
    data = _api("POST", "/users", {
        "first_name": "Juan",
        "last_name": "Pérez",
        "username": "juan.perez.qa",
        "email": "juan.perez.qa@test.local",
        "password": "TestPass123!",
        "activated": True,
    })
    user = data.get("payload", {})
    yield user
    if user.get("id"):
        _api("DELETE", f"/users/{user['id']}")


@pytest.fixture
def user_ana():
    """Creates the test user Ana López."""
    data = _api("POST", "/users", {
        "first_name": "Ana",
        "last_name": "López",
        "username": "ana.lopez.qa",
        "email": "ana.lopez.qa@test.local",
        "password": "TestPass123!",
        "activated": True,
    })
    user = data.get("payload", {})
    yield user
    if user.get("id"):
        _api("DELETE", f"/users/{user['id']}")


# ---------------------------------------------------------------------------
# Expose BASE_URL to all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL
