"""
CP-HU01-11 – Validación de campo obligatorio Asset Tag vacío
CP-HU01-12 – Bloqueo de creación de activo con Asset Tag duplicado
CP-HU01-13 – Bloqueo de creación con Asset Name mayor a 255 caracteres
CP-HU01-14 – Bloqueo de creación con modelo inexistente o no disponible
CP-HU01-15 – El detalle del activo creado conserva categoría, modelo, serial, ubicación y estado

Assigned to: Ignacio Alpízar Villalobos
"""
import uuid
import pytest
from conftest import get_asset_by_serial, delete_assets_by_serial, _api
from pages.asset_create_page import AssetCreatePage
from pages.asset_detail_page import AssetDetailPage


# ---------------------------------------------------------------------------
# CP-HU01-11
# ---------------------------------------------------------------------------

@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu01_11_asset_tag_vacio(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que Snipe-IT no permite crear un activo cuando el campo Asset Tag
    queda vacío, ya que es un identificador obligatorio del activo.
    Técnica: Caja negra / Partición de equivalencia – campo obligatorio vacío.
    """
    serial = f"SN-AST-1011-{uuid.uuid4().hex[:6]}"
    asset_registry.append(serial)

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag="",                            # campo obligatorio vacío
        name="Laptop sin tag QA",
        serial=serial,
        model_id=asset_prereqs["model_id"],      model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    # El sistema no debe redirigir a éxito
    assert "created successfully" not in create.page_text(), (
        "El activo NO debería haberse creado con Asset Tag vacío"
    )
    errors = create.get_validation_errors()
    assert any("asset tag" in e.lower() or "required" in e.lower() or "requerido" in e.lower()
               for e in errors), (
        f"Se esperaba error de campo requerido para Asset Tag. Errores: {errors}"
    )


# ---------------------------------------------------------------------------
# CP-HU01-12
# ---------------------------------------------------------------------------

@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu01_12_asset_tag_duplicado(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que el sistema no permite registrar un activo cuando el Asset Tag
    ya pertenece a otro activo activo en inventario.
    Técnica: Caja negra / Prueba negativa – unicidad del identificador.
    """
    dup_tag = f"AST-DUP-{uuid.uuid4().hex[:6]}"
    serial_base = f"SN-AST-DUP-BASE-{uuid.uuid4().hex[:6]}"
    serial_dup  = f"SN-AST-DUP-NEW-{uuid.uuid4().hex[:6]}"
    asset_registry.append(serial_base)
    asset_registry.append(serial_dup)

    # Crear activo base con el tag que luego duplicaremos
    _api("POST", "/hardware", {
        "asset_tag":       dup_tag,
        "name":            "Activo existente tag duplicado",
        "serial":          serial_base,
        "model_id":        asset_prereqs["model_id"],
        "status_id":       asset_prereqs["status_id"],
        "rtd_location_id": asset_prereqs["location_id"],
    })

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=dup_tag,                       # tag duplicado
        name="Laptop tag duplicado QA",
        serial=serial_dup,
        model_id=asset_prereqs["model_id"],      model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    assert "created successfully" not in create.page_text(), (
        "El activo NO debería haberse creado con Asset Tag duplicado"
    )
    errors = create.get_validation_errors()
    assert any(kw in e.lower() for e in errors for kw in ("taken", "duplic", "unique")), (
        f"Se esperaba error de duplicidad para Asset Tag. Errores: {errors}"
    )


# ---------------------------------------------------------------------------
# CP-HU01-13
# ---------------------------------------------------------------------------

@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
@pytest.mark.xfail(
    strict=True,
    reason=(
        "DEF-US01-01: El campo Asset Name tiene maxlength=191 (columna varchar(191)). "
        "Snipe-IT acepta el nombre de 256 caracteres mediante automatización (Playwright "
        "bypasea maxlength) y lo almacena truncado a 191 sin mostrar error de validación. "
        "Ver evidence/DEF-US05-01_garantia_dia_actual.md"
    ),
)
def test_cp_hu01_13_asset_name_mayor_255(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que el sistema rechaza un Asset Name que supera el límite máximo
    de 255 caracteres, mostrando un error de longitud máxima.
    Técnica: Análisis de valores límite – límite superior inválido.

    HALLAZGO (DEF-US01-01 – compartido con Aarón): Snipe-IT v8.4.0 no valida
    la longitud del nombre en el servidor. Al enviar 256 caracteres omitiendo
    el maxlength del cliente, el activo se crea con el nombre truncado a 191
    caracteres sin ningún mensaje de error. Este test queda xfail(strict).
    """
    tag    = f"AST-HU01-1013-{uuid.uuid4().hex[:6]}"
    serial = f"SN-AST-1013-{uuid.uuid4().hex[:6]}"
    asset_registry.append(serial)

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name="A" * 256,
        serial=serial,
        model_id=asset_prereqs["model_id"],      model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    assert "created successfully" not in create.page_text().lower(), (
        "DEFECTO: El sistema aceptó Asset Name de 256 caracteres sin rechazarlo."
    )
    assert any(kw in create.page_text().lower() for kw in ("255", "191", "max", "characters", "caracteres")), (
        "Se esperaba mensaje de error de longitud máxima."
    )


# ---------------------------------------------------------------------------
# CP-HU01-14
# ---------------------------------------------------------------------------

@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu01_14_modelo_inexistente(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que Snipe-IT no permite crear un activo si no se selecciona un
    modelo válido (campo Model obligatorio).
    Técnica: Caja negra / Prueba negativa – referencia inexistente.
    """
    serial = f"SN-AST-1014-{uuid.uuid4().hex[:6]}"
    asset_registry.append(serial)

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=f"AST-HU01-1014-{uuid.uuid4().hex[:6]}",
        name="Laptop modelo inexistente QA",
        serial=serial,
        model_id=None,                           # sin modelo
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    assert "created successfully" not in create.page_text(), (
        "El activo NO debería haberse creado sin Modelo"
    )
    errors = create.get_validation_errors()
    assert any("model" in e.lower() or "required" in e.lower() or "requerido" in e.lower()
               for e in errors), (
        f"Se esperaba error de campo requerido para Model. Errores: {errors}"
    )


# ---------------------------------------------------------------------------
# CP-HU01-15
# ---------------------------------------------------------------------------

@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu01_15_detalle_conserva_datos(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que, después de crear un activo exitosamente, la vista de detalle
    muestra exactamente la misma información ingresada durante el registro.
    Técnica: Consistencia entre vistas – formulario de creación vs. detalle.
    """
    suffix = uuid.uuid4().hex[:8]
    tag    = f"AST-HU01-1015-{suffix}"
    serial = f"SN-AST-1015-{suffix}"
    asset_registry.append(serial)

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    # Redirect to asset detail after save
    create.page.evaluate(
        "() => { const s = document.querySelector('select[name=\"redirect_option\"]'); "
        "if (s) { s.value = 'item'; if (window.jQuery) jQuery(s).trigger('change'); } }"
    )
    create.fill_form(
        asset_tag=tag,
        name="Laptop detalle QA",
        serial=serial,
        model_id=asset_prereqs["model_id"],      model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    # Verificar que llegamos a la vista de detalle
    detail_text = create.page.locator("body").inner_text(timeout=8000)

    assert tag               in detail_text, f"Asset Tag '{tag}' no aparece en el detalle"
    assert "Laptop detalle QA" in detail_text, "Asset Name no aparece en el detalle"
    assert "Dell Latitude 5420" in detail_text, "Modelo no aparece en el detalle"
    assert serial            in detail_text, f"Serial '{serial}' no aparece en el detalle"
    assert "Ready to Deploy" in detail_text, "Status no aparece en el detalle"
