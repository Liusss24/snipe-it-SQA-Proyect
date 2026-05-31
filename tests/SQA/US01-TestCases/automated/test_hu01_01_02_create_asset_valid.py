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
@pytest.mark.xfail(
    reason="DEF-US01-01: El campo Asset Name tiene maxlength=191 (columna varchar(191)). "
           "El Plan de Pruebas asume un límite de 255; el sistema real trunca a 191. "
           "Ver evidence/DEF-US01-01_asset_name_length.md",
    strict=True,
)
def test_cp_hu01_02_creacion_asset_name_255_caracteres(
    auth_page, base_url, asset_prereqs, asset_registry
):
    """
    Verifica que el sistema permite guardar un activo cuando Asset Name
    contiene exactamente 255 caracteres (límite superior válido según el Plan).
    Técnica: Análisis de valores límite.

    HALLAZGO (DEF-US01-01): Snipe-IT limita Asset Name a 191 caracteres
    (atributo HTML maxlength=191 + columna `assets.name` varchar(191)). El campo
    de entrada IMPIDE escribir 255 caracteres y el valor se almacena truncado a
    191. Por tanto el límite superior válido REAL es 191, no 255. Este test queda
    marcado como xfail(strict) documentando la discrepancia entre el Plan de
    Pruebas y el comportamiento del sistema: si algún día el sistema aceptara 255,
    el test pasaría inesperadamente (XPASS) y nos avisaría de revisar el Plan.
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

    # El sistema acepta el guardado, pero el nombre se trunca: el activo existe...
    asset = get_asset_by_serial(serial)
    assert asset is not None, "El activo no quedó registrado"

    # ...y aquí está el assert que el Plan espera (255). Falla por el truncado a
    # 191 (DEF-US01-01) -> xfail esperado.
    assert len(asset.get("name") or "") == 255, (
        f"El nombre almacenado no tiene 255 caracteres: {len(asset.get('name') or '')} "
        f"(DEF-US01-01: el sistema trunca a 191)"
    )


@pytest.mark.sistema
@pytest.mark.medium
def test_cp_hu01_02b_limite_real_191_caracteres(
    auth_page, base_url, asset_prereqs, asset_registry
):
    """
    Test complementario que documenta el límite REAL del sistema (191 caracteres).
    Confirma que en el borde real (191) el activo se crea y el nombre se conserva
    completo. Sirve como caso de valores límite ajustado al comportamiento real
    y deja constancia objetiva del defecto DEF-US01-01.
    """
    serial = "SN-AST-1002B"
    asset_registry.append(serial)
    tag = f"QA-1002B-{uuid.uuid4().hex[:6]}"
    name_191 = "A" * 191

    create = AssetCreatePage(auth_page, base_url)
    create.navigate()
    create.fill_form(
        asset_tag=tag,
        name=name_191,
        serial=serial,
        model_id=asset_prereqs["model_id"],     model_name=asset_prereqs["model_name"],
        status_id=asset_prereqs["status_id"],    status_name=asset_prereqs["status_name"],
        location_id=asset_prereqs["location_id"], location_name=asset_prereqs["location_name"],
    )
    create.submit()

    flash = create.get_flash_message()
    assert "created successfully" in flash.lower(), (
        f"El sistema debió aceptar un Asset Name de 191 caracteres. Flash: {flash!r}"
    )

    asset = get_asset_by_serial(serial)
    assert asset is not None, "El activo de 191 caracteres no quedó registrado"
    assert len(asset.get("name") or "") == 191, (
        f"El nombre de 191 caracteres no se conservó completo: "
        f"{len(asset.get('name') or '')}"
    )
