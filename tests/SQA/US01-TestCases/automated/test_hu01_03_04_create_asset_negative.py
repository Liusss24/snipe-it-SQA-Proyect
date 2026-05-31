"""
CP-HU01-03 – Bloqueo de creación de activo con serial duplicado
CP-HU01-04 – El formulario no permite guardar un activo sin Status Label
"""
import uuid
import pytest
from conftest import count_assets_by_serial, asset_exists_by_serial
from pages.asset_create_page import AssetCreatePage


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu01_03_bloqueo_serial_duplicado(
    auth_page, base_url, asset_prereqs, existing_asset, unique_serial_enabled
):
    """
    Verifica que Snipe-IT no permite crear un activo nuevo cuando el Serial
    ya existe en otro activo registrado.
    Técnica: Prueba negativa / Unicidad e integridad referencial.

    Precondición: el ajuste 'unique_serial' debe estar activo (gestionado por
    el fixture unique_serial_enabled). Ya existe un activo con SN-001234.
    """
    serial = existing_asset["serial"]  # SN-001234
    assert count_assets_by_serial(serial) == 1, "Precondición: debe existir 1 activo con ese serial"

    tag = f"QA-DUP-{uuid.uuid4().hex[:6]}"
    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name="Laptop duplicada QA",
        serial=serial,
        model_id=asset_prereqs["model_id"],      model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],     status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    # No debe mostrarse confirmación de éxito
    flash = create.get_flash_message()
    assert "created successfully" not in flash.lower(), (
        "El sistema no debió crear un activo con serial duplicado"
    )

    # Verificación PRINCIPAL: no debe quedar un segundo activo con ese serial.
    # Con unique_serial activo, Snipe-IT rechaza la creación (la cantidad de
    # activos con SN-001234 se mantiene en 1).
    assert count_assets_by_serial(serial) == 1, (
        "Se creó un segundo activo con serial duplicado (la unicidad no se respetó)"
    )

    # Verificación secundaria (UX): comprobar si el sistema comunica la unicidad.
    # HALLAZGO: con unique_serial activo, Snipe-IT bloquea el duplicado pero
    # redirige al listado SIN mostrar un mensaje claro de "serial duplicado".
    page_text = create.page_text()
    errors = " ".join(create.get_validation_errors()).lower()
    mensaje_unicidad = any(
        s in (page_text + errors)
        for s in ("must be unique", "already been taken", "serial must be unique")
    )
    if not mensaje_unicidad:
        print(
            "[CP-HU01-03] HALLAZGO UX: el duplicado fue rechazado (no se creó el "
            "activo) pero la UI no mostró un mensaje de unicidad de serial."
        )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu01_04_no_permite_guardar_sin_status_label(
    auth_page, base_url, asset_prereqs, asset_registry
):
    """
    Verifica que el sistema no permite crear un activo si el campo obligatorio
    Status Label no ha sido seleccionado.
    Técnica: Caja negra / Prueba negativa.
    """
    serial = "SN-AST-1003"
    asset_registry.append(serial)  # por si el sistema lo creara indebidamente, se limpia
    tag = f"QA-1003-{uuid.uuid4().hex[:6]}"

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    # IMPORTANTE: status_id se deja sin seleccionar
    create.fill_form(
        asset_tag=tag,
        name="Laptop sin status QA",
        serial=serial,
        model_id=asset_prereqs["model_id"],      model_name=asset_prereqs["model_name"],
        status_id=None,
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    # No debe mostrarse confirmación de éxito
    flash = create.get_flash_message()
    assert "created successfully" not in flash.lower(), (
        "El sistema no debió crear un activo sin Status Label"
    )

    # Debe permanecer en el formulario o mostrar validación del campo requerido
    errors = " ".join(create.get_validation_errors()).lower()
    on_form = create.is_on_create_form()
    status_validation = "status" in errors or on_form
    assert status_validation, (
        f"No se exigió el Status Label. on_form={on_form}, errores={errors!r}"
    )

    # El activo no debe quedar registrado
    assert not asset_exists_by_serial(serial), (
        "Se creó un activo pese a no tener Status Label"
    )
