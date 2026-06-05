import os
import time
import uuid
import subprocess
import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import Playwright, Page, BrowserContext

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

BASE_URL        = os.getenv("SNIPEIT_BASE_URL",       "http://localhost:8000")
ADMIN_USERNAME  = os.getenv("SNIPEIT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD  = os.getenv("SNIPEIT_ADMIN_PASSWORD", "password")
API_TOKEN       = os.getenv("SNIPEIT_API_TOKEN",      "")
NOPERM_USERNAME = os.getenv("SNIPEIT_NOPERM_USERNAME", "viewer")
NOPERM_PASSWORD = os.getenv("SNIPEIT_NOPERM_PASSWORD", "password")

DB_CONTAINER    = os.getenv("SNIPEIT_DB_CONTAINER",   "snipeit-db-1")
DB_NAME         = os.getenv("SNIPEIT_DB_NAME",        "snipeit_db")
DB_USER         = os.getenv("SNIPEIT_DB_USER",        "snipeit_user")
DB_PASS         = os.getenv("SNIPEIT_DB_PASS",        "")

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
            time.sleep(8 * (attempt + 1))   # 8s, 16s
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Find-or-create helper (added by Ignacio Alpízar – handles existing data)
# ---------------------------------------------------------------------------

def _find_or_create(endpoint: str, name: str, create_data: dict) -> dict:
    """GET existing entity by name or POST to create it. Returns the payload dict.

    Snipe-IT's POST endpoints return payload=null when the entity already exists
    (unique constraint). This helper searches first to avoid that issue.
    """
    search_ep = endpoint.split("?")[0]
    rows = _api("GET", f"/{search_ep}?limit=100").get("rows", [])
    existing = next((r for r in rows if r.get("name") == name), None)
    if existing:
        return existing
    return _api("POST", f"/{search_ep}", create_data).get("payload") or {}


# ---------------------------------------------------------------------------
# Asset query helpers (source of truth for assertions)
# ---------------------------------------------------------------------------

def find_assets_by_serial(serial: str) -> list[dict]:
    """Returns the list of assets whose serial matches exactly."""
    rows = _api("GET", f"/hardware?search={serial}&limit=50").get("rows", [])
    return [r for r in rows if (r.get("serial") or "") == serial]


def asset_exists_by_serial(serial: str) -> bool:
    return len(find_assets_by_serial(serial)) > 0


def count_assets_by_serial(serial: str) -> int:
    return len(find_assets_by_serial(serial))


def get_asset_by_serial(serial: str) -> dict | None:
    matches = find_assets_by_serial(serial)
    return matches[0] if matches else None


def delete_assets_by_serial(serial: str) -> None:
    for a in find_assets_by_serial(serial):
        if a.get("id"):
            try:
                _api("DELETE", f"/hardware/{a['id']}")
            except Exception:
                pass


def find_assets_by_tag(tag: str) -> list[dict]:
    """Returns assets whose asset_tag matches exactly."""
    rows = _api("GET", f"/hardware?search={tag}&limit=50").get("rows", [])
    return [r for r in rows if (r.get("asset_tag") or "") == tag]


def get_asset_activity(asset_id: int) -> list[dict]:
    """Returns the action log entries for a given asset.
    Snipe-IT v8 does not expose /hardware/{id}/activity.
    The correct endpoint is /reports/activity filtered by item_type + item_id.
    """
    return _api("GET", f"/reports/activity?item_type=asset&item_id={asset_id}&limit=50").get("rows", [])


def _status_id_by_name(name: str) -> int:
    rows = _api("GET", "/statuslabels?limit=50").get("rows", [])
    for r in rows:
        if r.get("name") == name:
            return r["id"]
    raise RuntimeError(f"Status label '{name}' not found in Snipe-IT.")


# ---------------------------------------------------------------------------
# DB helper para el ajuste unique_serial (necesario en CP-HU01-03)
# ---------------------------------------------------------------------------

def _db_query(sql: str) -> str:
    """Ejecuta SQL en el contenedor MariaDB y devuelve stdout (sin cabeceras)."""
    result = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "mariadb",
         "-u", DB_USER, f"-p{DB_PASS}", DB_NAME, "-N", "-s", "-e", sql],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"DB query failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _get_unique_serial() -> int:
    return int(_db_query("SELECT unique_serial FROM settings WHERE id=1;") or "0")


def _set_unique_serial(value: int) -> None:
    _db_query(f"UPDATE settings SET unique_serial={int(value)} WHERE id=1;")


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
    """Page logged in as the restricted user (viewer) — no asset-create permissions."""
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
# Prerequisite master data (created once per session, cleaned at the end)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def asset_prereqs():
    """
    Crea los datos maestros que exigen las precondiciones de la US01:
      - Categoría 'Laptops' (tipo asset)
      - Fabricante 'Dell'
      - Modelo 'Dell Latitude 5420' (asociado a Laptops)
      - Ubicación 'Oficina Central'
      - Status Label 'Ready to Deploy' (reutiliza el existente)
    Devuelve un dict con ids y nombres. Limpia todo al final de la sesión.
    """
    created = {}

    cat = _find_or_create("categories", "Laptops", {
        "name": "Laptops", "category_type": "asset",
    })
    created["category_id"] = cat.get("id")

    man = _find_or_create("manufacturers", "Dell", {"name": "Dell"})
    created["manufacturer_id"] = man.get("id")

    model = _find_or_create("models", "Dell Latitude 5420", {
        "name": "Dell Latitude 5420",
        "category_id": created["category_id"],
        "manufacturer_id": created["manufacturer_id"],
        "model_number": "LAT-5420",
    })
    created["model_id"] = model.get("id")
    created["model_name"] = "Dell Latitude 5420"

    loc = _find_or_create("locations", "Oficina Central", {"name": "Oficina Central"})
    created["location_id"] = loc.get("id")
    created["location_name"] = "Oficina Central"

    created["status_id"] = _status_id_by_name("Ready to Deploy")
    created["status_name"] = "Ready to Deploy"
    created["category_name"] = "Laptops"

    yield created

    # Teardown (orden inverso por dependencias)
    for ep, key in [
        ("models", "model_id"),
        ("categories", "category_id"),
        ("manufacturers", "manufacturer_id"),
        ("locations", "location_id"),
    ]:
        if created.get(key):
            try:
                _api("DELETE", f"/{ep}/{created[key]}")
                time.sleep(0.4)
            except Exception:
                pass


@pytest.fixture
def asset_registry():
    """
    Registro de seriales creados durante un test. En el teardown elimina
    cualquier activo con esos seriales (idempotente, evita basura).
    """
    serials: list[str] = []
    yield serials
    for s in serials:
        delete_assets_by_serial(s)
        time.sleep(0.3)


@pytest.fixture
def unique_serial_enabled():
    """
    Activa el ajuste 'unique_serial' de Snipe-IT (necesario para que el sistema
    rechace seriales duplicados en CP-HU01-03) y restaura el valor original al
    finalizar. Si Docker/BD no está accesible, hace skip del test con un mensaje
    claro en vez de fallar de forma engañosa.
    """
    try:
        original = _get_unique_serial()
    except Exception as e:
        pytest.skip(f"No se pudo leer el ajuste unique_serial vía Docker/BD: {e}")
        return

    if original != 1:
        _set_unique_serial(1)
    yield
    # Restaurar el valor original
    try:
        _set_unique_serial(original)
    except Exception:
        pass


@pytest.fixture
def existing_asset(asset_prereqs):
    """
    Crea por API un activo con serial SN-001234 (precondición de CP-HU01-03)
    y lo elimina al finalizar.
    """
    serial = "SN-001234"
    delete_assets_by_serial(serial)  # asegura estado limpio previo
    tag = f"QA-EXIST-{uuid.uuid4().hex[:6]}"
    payload = _api("POST", "/hardware", {
        "asset_tag": tag,
        "model_id": asset_prereqs["model_id"],
        "status_id": asset_prereqs["status_id"],
        "name": "Activo existente QA",
        "serial": serial,
        "rtd_location_id": asset_prereqs["location_id"],
    }).get("payload", {})
    yield {"serial": serial, "asset_tag": tag, "id": payload.get("id")}
    delete_assets_by_serial(serial)
