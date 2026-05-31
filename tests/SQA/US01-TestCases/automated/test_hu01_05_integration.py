"""
CP-HU01-05 – El activo recién creado aparece en Assets con estado Ready to Deploy
"""
import uuid
import pytest
from conftest import get_asset_by_serial
from pages.asset_create_page import AssetCreatePage
from pages.asset_list_page import AssetListPage


@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu01_05_activo_aparece_en_listado(
    auth_page, base_url, asset_prereqs, asset_registry
):
    """
    Verifica que un activo creado exitosamente se refleje luego en el listado
    general de Assets, manteniendo consistencia de serial, modelo y estado.
    Técnica: Caja negra / Consistencia entre módulos (integración).
    """
    serial = "SN-AST-2001"
    asset_registry.append(serial)
    tag = f"QA-2001-{uuid.uuid4().hex[:6]}"

    # Paso 1-6: crear el activo
    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name="Laptop QA Integracion",
        serial=serial,
        model_id=asset_prereqs["model_id"],      model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],     status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()
    flash = create.get_flash_message()
    assert "created successfully" in flash.lower(), f"La creación previa falló: {flash!r}"

    # Paso 7-9: buscar el activo en el listado general
    lst = AssetListPage(auth_page, base_url)
    lst.navigate()
    lst.search(serial)

    row = lst.find_row(serial)
    assert row is not None, f"El activo {serial} no aparece en el listado de Assets"

    # Consistencia entre módulos: el listado refleja modelo y estado correctos
    row_text = row.first.inner_text()
    assert "Dell Latitude 5420" in row_text, (
        f"El modelo no coincide en el listado. Fila: {row_text!r}"
    )
    assert "Ready to Deploy" in row_text, (
        f"El estado no coincide en el listado. Fila: {row_text!r}"
    )

    # Fuente de verdad (API): los datos coinciden con lo ingresado
    asset = get_asset_by_serial(serial)
    assert asset is not None
    assert (asset.get("model") or {}).get("name") == "Dell Latitude 5420"
    assert (asset.get("status_label") or {}).get("name") == "Ready to Deploy"
    assert (asset.get("category") or {}).get("name") == "Laptops"
