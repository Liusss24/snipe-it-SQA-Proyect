import os
import time
import uuid
import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import Playwright, Page, BrowserContext

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

BASE_URL        = os.getenv("SNIPEIT_BASE_URL",       "http://localhost:8000")
ADMIN_USERNAME  = os.getenv("SNIPEIT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD  = os.getenv("SNIPEIT_ADMIN_PASSWORD", "password")
API_TOKEN       = os.getenv("SNIPEIT_API_TOKEN",      "")
NOPERM_USERNAME = os.getenv("SNIPEIT_NOPERM_USERNAME","viewer")
NOPERM_PASSWORD = os.getenv("SNIPEIT_NOPERM_PASSWORD","password")

# ---------------------------------------------------------------------------
# API helper
# ---------------------------------------------------------------------------

def _api(method: str, endpoint: str, data: dict | None = None, retries: int = 3) -> dict:
    """Calls the Snipe-IT REST API. Retries up to 3 times on 429 (rate limit)."""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    url = f"{BASE_URL}/api/v1{endpoint}"
    for attempt in range(retries):
        resp = requests.request(method, url, json=data, headers=headers, timeout=10)
        if resp.status_code == 429 and attempt < retries - 1:
            time.sleep(8 * (attempt + 1))   # 8s, 16s – respects Snipe-IT's rate limit window
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return resp.json()


def get_free_seats(license_id: int) -> int:
    return _api("GET", f"/licenses/{license_id}").get("free_seats_count", 0)


def get_checked_out_count(license_id: int) -> int:
    return _api("GET", f"/licenses/{license_id}/seats?status=assigned").get("total", 0)


def can_checkout(license_id: int) -> bool:
    return _api("GET", f"/licenses/{license_id}").get("available_actions", {}).get("checkout", False)


def user_has_license(user_id: int, license_name: str) -> bool:
    rows = _api("GET", f"/users/{user_id}/licenses?limit=50").get("rows", [])
    return any(r.get("name") == license_name for r in rows)


_category_id_cache: int | None = None

def _first_category_id() -> int:
    global _category_id_cache
    if _category_id_cache is None:
        rows = _api("GET", "/categories?limit=1&category_type=license").get("rows", [])
        if not rows:
            raise RuntimeError(
                "No license category found. Create at least one in Snipe-IT before running tests."
            )
        _category_id_cache = rows[0]["id"]
    return _category_id_cache


def _create_user(first: str, last: str) -> dict:
    """Creates a test user with a unique username. Skips the test on failure."""
    time.sleep(1.2)
    uid = uuid.uuid4().hex[:8]
    data = _api("POST", "/users", {
        "first_name": first, "last_name": last,
        "username": f"{first.lower()}.{last.lower()}.{uid}",
        "email": f"{first.lower()}.{last.lower()}.{uid}@test.local",
        "password": "TestPass123!",
        "password_confirmation": "TestPass123!",
        "activated": True,
    })
    user = data.get("payload") or {}
    if not user.get("id"):
        pytest.skip(f"Could not create test user {first} {last}: {data}")
    return user


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
    p = context.new_page()
    p.goto(f"{BASE_URL}/login")
    p.fill("input[name='username']", ADMIN_USERNAME)
    p.fill("input[name='password']", ADMIN_PASSWORD)
    p.click("button[type='submit']")
    p.wait_for_url(f"{BASE_URL}/**", wait_until="load")
    return p


@pytest.fixture(scope="function")
def noperm_page(context: BrowserContext) -> Page:
    p = context.new_page()
    p.goto(f"{BASE_URL}/login")
    p.fill("input[name='username']", NOPERM_USERNAME)
    p.fill("input[name='password']", NOPERM_PASSWORD)
    p.click("button[type='submit']")
    p.wait_for_url(f"{BASE_URL}/**", wait_until="load")
    return p


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


# ---------------------------------------------------------------------------
# Test-data fixtures
# ---------------------------------------------------------------------------

def _make_license(name: str, seats: int) -> dict:
    time.sleep(1.2)
    cat_id = _first_category_id()
    data = _api("POST", "/licenses", {"name": name, "seats": seats, "category_id": cat_id})
    lic = data.get("payload") or {}
    if not lic.get("id"):
        pytest.skip(f"Could not create license {name}: {data}")
    return lic


@pytest.fixture
def license_2_seats():
    lic = _make_license("LIC-HU04-01", 2)
    yield lic
    _api("DELETE", f"/licenses/{lic['id']}")


@pytest.fixture
def license_1_seat():
    lic = _make_license("LIC-HU04-02", 1)
    yield lic
    _api("DELETE", f"/licenses/{lic['id']}")


@pytest.fixture
def license_0_seats():
    """License with 0 free seats: creates a 1-seat license and checks it out via seat PATCH."""
    lic = _make_license("LIC-HU04-03", 1)
    lic_id = lic["id"]
    tmp_user = _create_user("Temp", "Seat")

    # Get the seat ID for this license, then assign via PATCH
    seats_resp = _api("GET", f"/licenses/{lic_id}/seats?status=available&limit=1")
    seat_id = (seats_resp.get("rows") or [{}])[0].get("id")
    if seat_id:
        _api("PATCH", f"/licenses/{lic_id}/seats/{seat_id}", {"assigned_to": tmp_user["id"]})

    yield lic
    time.sleep(0.4)
    _api("DELETE", f"/users/{tmp_user['id']}")
    time.sleep(0.4)
    _api("DELETE", f"/licenses/{lic_id}")


@pytest.fixture
def user_juan():
    user = _create_user("Juan", "Perez")
    yield user
    _api("DELETE", f"/users/{user['id']}")


@pytest.fixture
def user_ana():
    user = _create_user("Ana", "Lopez")
    yield user
    _api("DELETE", f"/users/{user['id']}")
