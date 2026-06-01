"""
CP-HU01-19 – Registro de creación del activo en el historial de acciones
CP-HU01-20 – Validación de sanitización del campo Asset Name ante entrada tipo script
"""
import uuid
import pytest
from conftest import get_asset_by_serial, get_asset_activity, asset_exists_by_serial, delete_assets_by_serial
from pages.asset_create_page import AssetCreatePage
from pages.asset_detail_page import AssetDetailPage


# ---------------------------------------------------------------------------
# CP-HU01-19
# ---------------------------------------------------------------------------

@pytest.mark.integracion
@pytest.mark.medium
def test_cp_hu01_19_registro_historial_creacion(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que, al crear un activo correctamente, Snipe-IT registra la acción
    de creación en el historial / Action Log del activo.
    Técnica: Validación de trazabilidad.

    Fuente de verdad: GET /api/v1/hardware/{id}/activity
    """
    serial = "SN-AST-1019"
    asset_registry.append(serial)
    tag = f"QA-1019-{uuid.uuid4().hex[:6]}"

    # Pasos 1-6: crear el activo por UI
    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name="Laptop historial QA",
        serial=serial,
        model_id=asset_prereqs["model_id"],   model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"], status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    flash = create.get_flash_message()
    assert "created successfully" in flash.lower(), (
        f"La creación del activo falló en la UI: {flash!r}"
    )

    # Paso 7: obtener el ID del activo creado (fuente de verdad: API)
    asset = get_asset_by_serial(serial)
    assert asset is not None, f"El activo {serial} no se encontró por API tras la creación"
    asset_id = asset["id"]

    # Pasos 8-10: consultar el historial de acciones del activo
    activity = get_asset_activity(asset_id)
    assert len(activity) > 0, (
        f"El historial del activo {asset_id} está vacío; se esperaba al menos una entrada de creación"
    )

    # Verificar que existe una entrada de tipo 'create new'
    # Snipe-IT v8 usa el endpoint /reports/activity?item_type=asset&item_id={id}
    # y registra la creación con action_type = "create new"
    action_types = [
        str(entry.get("action_type", "") or entry.get("action", "")).lower()
        for entry in activity
    ]
    create_entry = any("create" in t for t in action_types)
    assert create_entry, (
        f"No se encontró entrada de tipo 'create new' en el historial. "
        f"Entradas encontradas: {action_types}"
    )

    # Verificar que el log está asociado al activo correcto
    for entry in activity:
        if "create" in str(entry.get("action_type", "") or entry.get("action", "")).lower():
            log_item = entry.get("item") or {}
            log_asset_id = log_item.get("id") if isinstance(log_item, dict) else None
            if log_asset_id is not None:
                assert log_asset_id == asset_id, (
                    f"El ID en el log ({log_asset_id}) no coincide con el activo creado ({asset_id})"
                )
            break


# ---------------------------------------------------------------------------
# CP-HU01-20
# ---------------------------------------------------------------------------

@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu01_20_sanitizacion_xss_asset_name(auth_page, base_url, asset_prereqs, asset_registry):
    """
    Verifica que Snipe-IT no ejecuta código HTML/JavaScript ingresado en el campo
    Asset Name durante la creación de un activo.
    Técnica: Prueba negativa / Validación de seguridad (XSS).

    El payload <script>alert("QA-PRUEBA")</script> no debe ejecutarse en ningún
    contexto: formulario de creación, vista de detalle ni listado de activos.
    """
    XSS_PAYLOAD = '<script>alert("QA-PRUEBA")</script>'
    serial = "SN-AST-1020"
    asset_registry.append(serial)
    tag = f"QA-1020-{uuid.uuid4().hex[:6]}"

    # Registrar un listener de diálogos ANTES de cualquier interacción
    dialog_messages: list[str] = []

    def on_dialog(dialog):
        dialog_messages.append(dialog.message)
        dialog.dismiss()

    auth_page.on("dialog", on_dialog)

    # Paso 1-7: navegar al formulario e ingresar el payload XSS en Asset Name
    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name=XSS_PAYLOAD,
        serial=serial,
        model_id=asset_prereqs["model_id"],   model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"], status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    # Paso 8: verificar que no apareció ningún alert() durante el submit
    assert len(dialog_messages) == 0, (
        f"Se ejecutó un script XSS durante el submit. Mensajes de alert: {dialog_messages}"
    )

    flash = create.get_flash_message()

    if "created successfully" in flash.lower():
        # El sistema guardó el input — verificar que lo muestra escapado (no ejecutado)
        asset = get_asset_by_serial(serial)
        assert asset is not None

        # Paso 9-10: navegar a la vista de detalle y verificar que el nombre aparece
        #            como texto plano escapado, sin ejecución de código
        detail = AssetDetailPage(auth_page, base_url)
        detail.navigate(asset["id"])
        auth_page.wait_for_timeout(800)

        assert len(dialog_messages) == 0, (
            f"El script XSS se ejecutó al cargar la vista de detalle: {dialog_messages}"
        )

        # Verificar que el contenido de la página contiene el texto escapado
        # (Snipe-IT/Blade escapa '<' y '>' como '&lt;' y '&gt;' en el HTML)
        page_html = detail.page_text()
        script_executed = "QA-PRUEBA" in page_html and "<script>" in page_html.lower()
        assert not script_executed, (
            "El payload XSS aparece sin escapar en el HTML de la vista de detalle"
        )

        # Paso 11: ir al listado de activos y verificar que tampoco se ejecuta ahí
        auth_page.goto(f"{base_url}/hardware")
        auth_page.wait_for_load_state("networkidle")
        auth_page.wait_for_timeout(800)

        assert len(dialog_messages) == 0, (
            f"El script XSS se ejecutó al cargar el listado de activos: {dialog_messages}"
        )

    else:
        # El sistema rechazó el input directamente — también es comportamiento correcto
        assert not asset_exists_by_serial(serial), (
            "El activo con payload XSS aparece en la API aunque el sistema mostró error"
        )
