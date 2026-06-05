"""
CP-HU05-08 – Activo con fecha EOL próxima genera alerta
CP-HU05-09 – Activo con garantía y EOL próximos no aparece duplicado
CP-HU05-10 – Activo archivado no genera alerta de vencimiento
"""
import uuid
import pytest
from conftest import (
    configure_alerts, create_asset, delete_asset_by_tag,
    run_expiring_alerts, today_minus, today_plus,
)


@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu05_08_eol_proximo_genera_alerta(alerts_enabled, asset_registry):
    """
    Verifica que un activo con Asset EOL Date dentro del umbral de 30 días
    aparece en el reporte de alertas (integración entre datos del activo y el
    comando de alertas).
    Técnica: Caja negra / Partición de equivalencia – valor válido.
    """
    tag = f"ACT-HU05-05-{uuid.uuid4().hex[:6]}"
    asset_registry.append(tag)
    create_asset(
        asset_tag=tag,
        name="Activo EOL proximo QA",
        serial=f"SN-HU05-05-{uuid.uuid4().hex[:6]}",
        eol_date=today_plus(5),
    )

    output = run_expiring_alerts()

    assert tag in output or "Activo EOL proximo QA" in output, (
        f"El activo '{tag}' con EOL en 5 días no aparece en alertas.\n{output}"
    )


@pytest.mark.integracion
@pytest.mark.medium
def test_cp_hu05_09_garantia_y_eol_no_duplica(alerts_enabled, asset_registry):
    """
    Verifica que un activo que cumple DOS condiciones de alerta (garantía próxima
    + EOL próximo) aparece una sola vez en el reporte (no se duplica).
    Técnica: Integración / Validación de duplicados.
    """
    tag = f"ACT-HU05-06-{uuid.uuid4().hex[:6]}"
    asset_registry.append(tag)
    create_asset(
        asset_tag=tag,
        name="Activo doble condicion QA",
        serial=f"SN-HU05-06-{uuid.uuid4().hex[:6]}",
        purchase_date=today_minus(356),
        warranty_months=12,
        eol_date=today_plus(5),
    )

    output = run_expiring_alerts()

    count = output.count(tag)
    assert count <= 1, (
        f"'{tag}' aparece {count} veces en el output; se esperaba máximo 1.\n{output}"
    )
    assert count == 1, (
        f"'{tag}' no aparece en el output aunque cumple condiciones de alerta.\n{output}"
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu05_10_activo_archivado_no_genera_alerta(alerts_enabled, asset_registry):
    """
    Verifica que un activo en estado Archivado no genera alerta aunque su garantía
    o fecha EOL estén dentro del umbral.
    Técnica: Caja negra / Valor inválido – estado Archived excluye el activo.
    """
    tag = f"ACT-HU05-07-{uuid.uuid4().hex[:6]}"
    asset_registry.append(tag)
    create_asset(
        asset_tag=tag,
        name="Activo archivado QA",
        serial=f"SN-HU05-07-{uuid.uuid4().hex[:6]}",
        eol_date=today_plus(5),
        archived=True,
    )

    output = run_expiring_alerts()

    assert tag not in output, (
        f"'{tag}' está archivado y NO debería generar alerta.\n{output}"
    )
