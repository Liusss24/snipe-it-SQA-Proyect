"""
CP-HU01-17 – Validación de campo obligatorio Location vacío
CP-HU01-18 – Bloqueo de creación con ubicación inexistente o no disponible
"""
import uuid
import pytest
from conftest import _api, asset_exists_by_serial, delete_assets_by_serial
from pages.asset_create_page import AssetCreatePage


# ---------------------------------------------------------------------------
# CP-HU01-17
# ---------------------------------------------------------------------------

@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
@pytest.mark.xfail(
    reason=(
        "DEF-US01-17: En Snipe-IT v8, el campo Default Location no es obligatorio. "
        "El sistema permite crear el activo sin ubicación, contradiciendo el plan de pruebas."
    ),
    strict=True,
)
def test_cp_hu01_17_bloqueo_sin_location(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que el sistema no permite crear un activo si el campo Location /
    Default Location se deja vacío.
    Técnica: Partición de equivalencia — valor inválido (campo requerido omitido).

    NOTA: Este test se marca xfail porque Snipe-IT no exige ubicación por defecto.
    Ver DEF-US01-17 en evidence/.
    """
    serial = "SN-AST-1017"
    asset_registry.append(serial)
    tag = f"QA-1017-{uuid.uuid4().hex[:6]}"

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    # Location se omite deliberadamente (location_id=None)
    create.fill_form(
        asset_tag=tag,
        name="Laptop sin ubicacion QA",
        serial=serial,
        model_id=asset_prereqs["model_id"],   model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"], status_name=asset_prereqs["status_name"],
        location_id=None,
    )
    create.submit()

    flash = create.get_flash_message()
    assert "created successfully" not in flash.lower(), (
        "El sistema no debería crear el activo sin ubicación"
    )

    errors = " ".join(create.get_validation_errors()).lower()
    on_form = create.is_on_create_form()
    location_validated = "location" in errors or on_form
    assert location_validated, (
        f"El sistema no exigió el campo Location. on_form={on_form}, errores={errors!r}"
    )

    assert not asset_exists_by_serial(serial), (
        "Se creó el activo sin ubicación cuando el sistema debería haberlo bloqueado"
    )


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu01_17b_sistema_permite_crear_sin_location(
    auth_page, base_url, asset_prereqs, asset_registry
):
    """
    Caso complementario: documenta el comportamiento REAL de Snipe-IT v8.
    El sistema permite crear el activo sin seleccionar Default Location.
    La ubicación queda en blanco (null) en la base de datos.
    Este es el comportamiento actual del sistema (hallazgo de diseño vs. plan).
    """
    serial = "SN-AST-1017B"
    asset_registry.append(serial)
    tag = f"QA-1017B-{uuid.uuid4().hex[:6]}"

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name="Laptop sin ubicacion QA complementario",
        serial=serial,
        model_id=asset_prereqs["model_id"],   model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"], status_name=asset_prereqs["status_name"],
        location_id=None,
    )
    create.submit()

    flash = create.get_flash_message()
    assert "created successfully" in flash.lower(), (
        f"Se esperaba que Snipe-IT permitiera crear sin ubicación, pero falló: {flash!r}"
    )
    assert asset_exists_by_serial(serial), (
        "El activo no fue encontrado por la API tras la creación sin ubicación"
    )


# ---------------------------------------------------------------------------
# CP-HU01-18
# ---------------------------------------------------------------------------

@pytest.mark.integracion
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu01_18_bloqueo_ubicacion_inexistente(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que Snipe-IT no permite crear un activo con una ubicación inexistente
    o no disponible, tanto desde la interfaz UI como mediante petición API directa.
    Técnica: Prueba negativa / Unicidad e integridad referencial.

    Enfoque 1 – UI: el Select2 de Location no muestra 'Ubicación QA Inexistente'
                     porque no existe; el formulario no puede enviarse con ese valor.
    Enfoque 2 – API: enviar rtd_location_id=999999 (ID inexistente) y verificar
                     que el activo no queda registrado con esa ubicación.
    """
    serial_ui  = "SN-AST-1018-UI"
    serial_api = "SN-AST-1018-API"
    asset_registry.append(serial_ui)
    asset_registry.append(serial_api)

    # --- Enfoque 1: UI — verificar que la opción inexistente no aparece en Select2 ---
    fake_location_name = "Ubicacion QA Inexistente"

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()

    # Intentar buscar la ubicación inexistente en el Select2 vía API de búsqueda de Playwright
    # Hacemos clic en el campo para abrir el dropdown, escribimos el nombre y verificamos
    # que no se retorna ningún resultado válido.
    auth_page.evaluate("""() => {
        const s = document.getElementById('rtd_location_id_location_select');
        if (s && window.$) {
            $(s).select2('open');
        }
    }""")
    auth_page.wait_for_timeout(500)

    search_input = auth_page.locator(".select2-search__field").last
    if search_input.count() > 0:
        search_input.fill(fake_location_name)
        auth_page.wait_for_timeout(1000)
        results = auth_page.locator(".select2-results__option")
        result_texts = [results.nth(i).inner_text().strip() for i in range(results.count())]
        exact_match = any(fake_location_name.lower() in t.lower() for t in result_texts)
        assert not exact_match, (
            f"La ubicación inexistente '{fake_location_name}' apareció en el selector: {result_texts}"
        )

    # Cerrar el dropdown si quedó abierto
    auth_page.keyboard.press("Escape")
    auth_page.wait_for_timeout(300)

    # --- Enfoque 2: API — enviar un rtd_location_id inexistente ---
    FAKE_LOCATION_ID = 999999
    tag_api = f"QA-1018-API-{uuid.uuid4().hex[:6]}"

    try:
        resp = _api("POST", "/hardware", {
            "asset_tag": tag_api,
            "name": "Laptop ubicacion inexistente QA",
            "model_id": asset_prereqs["model_id"],
            "status_id": asset_prereqs["status_id"],
            "serial": serial_api,
            "rtd_location_id": FAKE_LOCATION_ID,
        })
        payload = resp.get("payload") or {}
        asset_id = payload.get("id")

        if asset_id:
            # El sistema aceptó la petición — verificar que no guardó la ubicación inválida
            asset_data = _api("GET", f"/hardware/{asset_id}")
            location_field = asset_data.get("rtd_location") or asset_data.get("location") or {}
            saved_location_id = location_field.get("id") if isinstance(location_field, dict) else None
            assert saved_location_id != FAKE_LOCATION_ID, (
                f"El sistema guardó el activo con rtd_location_id={FAKE_LOCATION_ID} "
                f"(ID inexistente), comprometiendo la integridad referencial."
            )
        else:
            # El sistema rechazó la petición — comportamiento correcto
            status = resp.get("status", "")
            assert status in ("error", ""), (
                f"Respuesta inesperada de la API al enviar ubicación inexistente: {resp}"
            )

    except Exception as exc:
        # Un error HTTP (422/400/500) también indica que el sistema rechazó la solicitud
        assert "422" in str(exc) or "400" in str(exc) or "500" in str(exc), (
            f"Error inesperado al enviar ubicación inexistente: {exc}"
        )
