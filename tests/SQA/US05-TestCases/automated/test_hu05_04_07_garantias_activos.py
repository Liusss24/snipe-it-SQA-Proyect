"""
CP-HU05-04 – Alerta por garantía de activo próxima a vencer
CP-HU05-05 – Garantía que vence hoy es incluida como alerta vigente
CP-HU05-06 – Activo sin fecha de compra no genera alerta de garantía
CP-HU05-07 – Activo sin meses de garantía no genera alerta de garantía
"""
import uuid
import pytest
from conftest import (
    configure_alerts, create_asset, delete_asset_by_tag,
    run_expiring_alerts, today_minus,
)


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu05_04_garantia_proxima_a_vencer(alerts_enabled, asset_registry):
    """
    Verifica que un activo cuya garantía calculada (purchase_date + warranty_months)
    cae dentro del umbral de 30 días genera alerta en snipeit:expiring-alerts.
    Técnica: Caja negra / Partición de equivalencia – valor válido.
    """
    tag = f"ACT-HU05-01-{uuid.uuid4().hex[:6]}"
    asset_registry.append(tag)
    # purchase_date hace 356 días → warranty 12 meses → vence en ~9 días
    create_asset(
        asset_tag=tag,
        name="Activo garantia proxima QA",
        serial=f"SN-HU05-01-{uuid.uuid4().hex[:6]}",
        purchase_date=today_minus(356),
        warranty_months=12,
    )

    output = run_expiring_alerts()

    assert tag in output or "Activo garantia proxima QA" in output, (
        f"El activo '{tag}' con garantía próxima no aparece en alertas.\n{output}"
    )


@pytest.mark.sistema
@pytest.mark.high
@pytest.mark.xfail(
    strict=True,
    reason=(
        "DEF-US05-01: getExpiringWarrantyOrEol() usa Carbon::now() (datetime con hora) "
        "en betweenIncluded(). Una garantía que vence hoy a medianoche (00:00:00) "
        "queda FUERA del rango cuando el test corre en cualquier momento posterior. "
        "El caso CP-HU05-05 exige que el día actual sea incluido. "
        "Ver evidence/DEF-US05-01_garantia_dia_actual.md"
    ),
)
def test_cp_hu05_05_garantia_vence_hoy(alerts_enabled, asset_registry):
    """
    Verifica que un activo cuya garantía vence exactamente el día actual
    es tratado como alerta vigente (límite inferior del umbral).
    Técnica: Análisis de valores límite – límite inferior.

    HALLAZGO (DEF-US05-01): Snipe-IT v8.4.0 usa Carbon::now() (con hora) en lugar
    de Carbon::today() (solo fecha). La garantía que vence hoy a las 00:00:00 queda
    fuera del rango betweenIncluded(now(), now()+30d) cuando la prueba corre de día.
    Este test queda xfail(strict) documentando la discrepancia: si el sistema corrije
    el bug y empieza a incluir el día actual, el test pasará (XPASS) y lo sabremos.
    """
    tag = f"ACT-HU05-02-{uuid.uuid4().hex[:6]}"
    asset_registry.append(tag)
    # purchase_date = hoy - 365d → purchase + 12 meses = hoy (00:00:00)
    create_asset(
        asset_tag=tag,
        name="Activo garantia vence hoy QA",
        serial=f"SN-HU05-02-{uuid.uuid4().hex[:6]}",
        purchase_date=today_minus(365),
        warranty_months=12,
    )

    output = run_expiring_alerts()

    assert tag in output or "Activo garantia vence hoy QA" in output, (
        f"DEF-US05-01: La garantía que vence HOY debería generar alerta. "
        f"El sistema la excluye por comparación datetime vs medianoche.\n{output}"
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu05_06_sin_fecha_compra_no_genera_alerta(alerts_enabled, asset_registry):
    """
    Verifica que un activo con Warranty Months configurado pero sin Purchase Date
    no produce alerta de garantía (no se puede calcular la fecha de vencimiento).
    Técnica: Caja negra / Valor inválido – datos incompletos.
    """
    tag = f"ACT-HU05-03-{uuid.uuid4().hex[:6]}"
    asset_registry.append(tag)
    create_asset(
        asset_tag=tag,
        name="Activo sin compra QA",
        serial=f"SN-HU05-03-{uuid.uuid4().hex[:6]}",
        purchase_date=None,
        warranty_months=12,
    )

    output = run_expiring_alerts()

    assert tag not in output, (
        f"'{tag}' no debería generar alerta sin Purchase Date.\n{output}"
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu05_07_sin_meses_garantia_no_genera_alerta(alerts_enabled, asset_registry):
    """
    Verifica que un activo con Purchase Date pero sin Warranty Months no produce
    alerta de garantía (no se puede calcular la fecha de vencimiento).
    Técnica: Caja negra / Valor inválido – datos incompletos.
    """
    tag = f"ACT-HU05-04-{uuid.uuid4().hex[:6]}"
    asset_registry.append(tag)
    create_asset(
        asset_tag=tag,
        name="Activo sin meses garantia QA",
        serial=f"SN-HU05-04-{uuid.uuid4().hex[:6]}",
        purchase_date=today_minus(356),
        warranty_months=None,
    )

    output = run_expiring_alerts()

    assert tag not in output, (
        f"'{tag}' no debería generar alerta sin Warranty Months.\n{output}"
    )
