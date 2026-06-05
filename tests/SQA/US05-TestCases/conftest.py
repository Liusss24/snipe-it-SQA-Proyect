"""
Shared fixtures for US05 – Alertas por vencimiento y garantía.

Strategy
--------
* Licenses and assets are created / deleted via the Snipe-IT REST API
  (same approach used by US01, US03, US04) to keep tests independent of
  internal DB state.
* Alert settings (enable / disable, email, interval) are managed via the
  `php artisan tinker` backend, because Snipe-IT exposes no public API
  endpoint for those settings.
* The artisan command `snipeit:expiring-alerts` is executed via subprocess
  to trigger the alert pipeline and capture its console output.

Environment variables (copy .env.example → .env and fill in):
  SNIPEIT_BASE_URL          http://localhost:8000
  SNIPEIT_ADMIN_USERNAME    admin
  SNIPEIT_ADMIN_PASSWORD    password
  SNIPEIT_API_TOKEN         <Passport JWT – see .env.example>
  SNIPEIT_ALERT_EMAIL       qa-alerts@example.test
  SNIPEIT_ARTISAN_PREFIX    docker exec proyecto_qa-app-1 php artisan
"""

import os
import shlex
import subprocess
import time
from datetime import date, timedelta

import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import Playwright, Page, BrowserContext

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

BASE_URL        = os.getenv("SNIPEIT_BASE_URL",       "http://localhost:8000").rstrip("/")
ADMIN_USERNAME  = os.getenv("SNIPEIT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD  = os.getenv("SNIPEIT_ADMIN_PASSWORD", "password")
API_TOKEN       = os.getenv("SNIPEIT_API_TOKEN",      "")
ALERT_EMAIL     = os.getenv("SNIPEIT_ALERT_EMAIL",    "qa-alerts@example.test")
ARTISAN_PREFIX  = shlex.split(
    os.getenv("SNIPEIT_ARTISAN_PREFIX", "docker exec proyecto_qa-app-1 php artisan")
)

# ---------------------------------------------------------------------------
# REST API helper
# ---------------------------------------------------------------------------

def _api(method: str, endpoint: str, data: dict | None = None, retries: int = 3) -> dict:
    """Calls the Snipe-IT REST API. Retries on 429 (rate-limit)."""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }
    url = f"{BASE_URL}/api/v1{endpoint}"
    for attempt in range(retries):
        resp = requests.request(method, url, json=data, headers=headers, timeout=15)
        if resp.status_code == 429 and attempt < retries - 1:
            time.sleep(8 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return resp.json()


def _api_payload(method: str, endpoint: str, data: dict | None = None) -> dict:
    """Like _api but returns the 'payload' sub-dict (Snipe-IT create/update responses)."""
    return _api(method, endpoint, data).get("payload", {})


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def today_plus(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def today_minus(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# Artisan helpers
# ---------------------------------------------------------------------------

def run_artisan(*args, timeout: int = 180) -> str:
    """Runs an artisan command inside the container and returns combined stdout+stderr."""
    cmd = ARTISAN_PREFIX + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (proc.stdout or "") + (proc.stderr or "")


def run_expiring_alerts() -> str:
    return run_artisan("snipeit:expiring-alerts")


def _tinker(php_code: str) -> str:
    """Executes a PHP snippet via artisan tinker and returns stdout."""
    script_path = "/tmp/qa_us05_tinker.php"
    # Write to container
    write_proc = subprocess.run(
        ARTISAN_PREFIX[:-2] + ["sh", "-c", f"cat > {script_path}"],
        input=f"<?php\n{php_code}\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    return run_artisan("tinker", script_path)


def configure_alerts(days: int = 30, email: str | None = None, enabled: int = 1) -> None:
    """Sets Snipe-IT alert settings via artisan tinker."""
    em = email or ALERT_EMAIL
    php = f"""
$s = App\\Models\\Setting::getSettings();
$s->alert_email     = '{em}';
$s->alerts_enabled  = {enabled};
$s->alert_interval  = {days};
$s->save();
echo 'ok';
"""
    _tinker(php)


def disable_alerts() -> None:
    configure_alerts(enabled=0, email=ALERT_EMAIL)


def clear_alert_email() -> None:
    php = """
$s = App\\Models\\Setting::getSettings();
$s->alert_email    = '';
$s->alerts_enabled = 1;
$s->save();
echo 'ok';
"""
    _tinker(php)


# ---------------------------------------------------------------------------
# License helpers (via REST API)
# ---------------------------------------------------------------------------

def _get_or_create_license_category() -> int:
    """Finds or creates the 'QA Software Licenses' category and returns its id."""
    rows = _api("GET", "/categories?limit=100&category_type=license").get("rows", [])
    for r in rows:
        if r.get("name") == "QA Software Licenses":
            return r["id"]
    cat = _api_payload("POST", "/categories", {
        "name": "QA Software Licenses",
        "category_type": "license",
    })
    return cat["id"]


def create_license(name: str, seats: int = 5, expiration_date: str | None = None,
                   termination_date: str | None = None) -> dict:
    """Creates a license via the API and returns the payload dict."""
    cat_id = _get_or_create_license_category()
    data: dict = {
        "name": name,
        "seats": seats,
        "serial": f"SER-{name}",
        "category_id": cat_id,
    }
    if expiration_date:
        data["expiration_date"] = expiration_date
    if termination_date:
        data["termination_date"] = termination_date
    return _api_payload("POST", "/licenses", data)


def delete_license_by_name(name: str) -> None:
    rows = _api("GET", f"/licenses?search={name}&limit=50").get("rows", [])
    for r in rows:
        if r.get("name") == name and r.get("id"):
            try:
                _api("DELETE", f"/licenses/{r['id']}")
                time.sleep(0.3)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Asset helpers (via REST API)
# ---------------------------------------------------------------------------

def _get_prereqs() -> dict:
    """Returns ids for category, model, location, status (creates if missing)."""
    # Category
    cats = _api("GET", "/categories?limit=100&category_type=asset").get("rows", [])
    cat = next((c for c in cats if c["name"] == "QA Laptops"), None)
    if not cat:
        cat = _api_payload("POST", "/categories", {"name": "QA Laptops", "category_type": "asset"})

    # Manufacturer
    mans = _api("GET", "/manufacturers?limit=100").get("rows", [])
    man = next((m for m in mans if m["name"] == "Dell"), None)
    if not man:
        man = _api_payload("POST", "/manufacturers", {"name": "Dell"})

    # Model
    models = _api("GET", "/models?limit=100").get("rows", [])
    model = next((m for m in models if m["name"] == "Dell Latitude 5420"), None)
    if not model:
        model = _api_payload("POST", "/models", {
            "name": "Dell Latitude 5420",
            "category_id": cat["id"],
            "manufacturer_id": man["id"],
            "model_number": "QA-5420",
        })

    # Location
    locs = _api("GET", "/locations?limit=100").get("rows", [])
    loc = next((l for l in locs if l["name"] == "Oficina Central"), None)
    if not loc:
        loc = _api_payload("POST", "/locations", {"name": "Oficina Central"})

    # Status
    statuses = _api("GET", "/statuslabels?limit=50").get("rows", [])
    status = next((s for s in statuses if s["name"] == "Ready to Deploy"), None)
    if not status:
        status = _api_payload("POST", "/statuslabels", {
            "name": "Ready to Deploy",
            "type": "deployable",
        })

    return {
        "category_id":   cat["id"],
        "model_id":      model["id"],   "model_name": "Dell Latitude 5420",
        "location_id":   loc["id"],     "location_name": "Oficina Central",
        "status_id":     status["id"], "status_name": "Ready to Deploy",
    }


def create_asset(asset_tag: str, name: str, serial: str,
                 purchase_date: str | None = None,
                 warranty_months: int | None = None,
                 eol_date: str | None = None,
                 archived: bool = False) -> dict:
    """Creates an asset via the REST API and returns the payload dict."""
    prereqs = _get_prereqs()
    data: dict = {
        "asset_tag":       asset_tag,
        "name":            name,
        "serial":          serial,
        "model_id":        prereqs["model_id"],
        "status_id":       prereqs["status_id"],
        "rtd_location_id": prereqs["location_id"],
    }
    if purchase_date:
        data["purchase_date"] = purchase_date
    if warranty_months is not None:
        data["warranty_months"] = warranty_months
    if eol_date:
        data["asset_eol_date"] = eol_date
    if archived:
        data["archived"] = 1
    return _api_payload("POST", "/hardware", data)


def delete_asset_by_tag(tag: str) -> None:
    rows = _api("GET", f"/hardware?search={tag}&limit=50").get("rows", [])
    for r in rows:
        if r.get("asset_tag") == tag and r.get("id"):
            try:
                _api("DELETE", f"/hardware/{r['id']}")
                time.sleep(0.3)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Browser fixtures (same pattern as US01 / US04)
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


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


# ---------------------------------------------------------------------------
# Alert configuration fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_alerts_after_test():
    """Re-enables alerts with default settings after every test so tests don't bleed state."""
    yield
    configure_alerts(days=30, email=ALERT_EMAIL, enabled=1)


@pytest.fixture
def alerts_enabled():
    """Ensures alerts are ON for this test (30-day threshold, test email)."""
    configure_alerts(days=30, email=ALERT_EMAIL, enabled=1)


@pytest.fixture
def alerts_disabled():
    """Disables alerts for this test."""
    disable_alerts()


@pytest.fixture
def alerts_no_email():
    """Clears the alert email field (alerts still enabled)."""
    clear_alert_email()


# ---------------------------------------------------------------------------
# License fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def lic_registry():
    """Tracks license names created in a test. Deletes them in teardown."""
    names: list[str] = []
    yield names
    for n in names:
        delete_license_by_name(n)
        time.sleep(0.2)


# ---------------------------------------------------------------------------
# Asset fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def asset_registry():
    """Tracks asset tags created in a test. Deletes them in teardown."""
    tags: list[str] = []
    yield tags
    for t in tags:
        delete_asset_by_tag(t)
        time.sleep(0.2)
