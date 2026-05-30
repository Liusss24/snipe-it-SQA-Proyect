"""
CP-HU01-01 – Creación exitosa de activo (Ready to Deploy)
CP-HU01-02 – Creación exitosa de activo con Asset Name de 255 caracteres
"""
import uuid
import pytest
from conftest import get_asset_by_serial
from pages.asset_create_page import AssetCreatePage


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu01_01_creacion_exitosa_ready_to_deploy(
    auth_page, base_url, asset_prereqs, asset_registry
):
    """
    Verifica que un usuario con permisos pueda crear un activo nuevo desde
    Assets > Create New con Model válido y Status Ready to Deploy.
    Técnica: Caja negra / Partición de equivalencia – valor válido.
    """
    serial = "SN-AST-1001"
    asset_registry.append(serial)
    tag = f"QA-1001-{uuid.uuid4().hex[:6]}"

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name="Laptop Dell 5420 - QA",
        serial=serial,
        model_id=asset_prereqs["model_id"],     model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    # Resultado esperado: mensaje de éxito
    flash = create.get_flash_message()
    assert "created successfully" in flash.lower(), (
        f"Se esperaba confirmación de creación. Flash: {flash!r}"
    )

    # El activo queda registrado con el estado y modelo correctos
    asset = get_asset_by_serial(serial)
    assert asset is not None, "El activo no aparece registrado vía API"
    assert (asset.get("status_label") or {}).get("name") == "Ready to Deploy", (
        f"El estado del activo no es Ready to Deploy: {asset.get('status_label')}"
    )
    assert (asset.get("model") or {}).get("name") == "Dell Latitude 5420", (
        f"El modelo del activo no coincide: {asset.get('model')}"
    )


@pytest.mark.sistema
@pytest.mark.medium
def test_cp_hu01_02_creacion_asset_name_255_caracteres(
    auth_page, base_url, asset_prereqs, asset_registry
):
    """
    Verifica que el sistema permite guardar un activo cuando Asset Name
    contiene exactamente 255 caracteres (límite superior válido).
    Técnica: Análisis de valores límite.
    """
    serial = "SN-AST-1002"
    asset_registry.append(serial)
    tag = f"QA-1002-{uuid.uuid4().hex[:6]}"
    name_255 = "A" * 255

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name=name_255,
        serial=serial,
        model_id=asset_prereqs["model_id"],     model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    # El sistema acepta el valor límite de 255 caracteres
    flash = create.get_flash_message()
    assert "created successfully" in flash.lower(), (
        f"El sistema debió aceptar un Asset Name de 255 caracteres. Flash: {flash!r}"
    )

    asset = get_asset_by_serial(serial)
    assert asset is not None, "El activo de 255 caracteres no quedó registrado"
    assert len(asset.get("name") or "") == 255, (
        f"El nombre almacenado no tiene 255 caracteres: {len(asset.get('name') or '')}"
    )
