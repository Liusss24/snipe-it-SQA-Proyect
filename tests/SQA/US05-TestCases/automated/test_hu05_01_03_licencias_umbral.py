"""
CP-HU05-01 – Alerta visible para licencia con vencimiento dentro de 30 días
CP-HU05-02 – Licencia que vence exactamente en el día límite genera alerta
CP-HU05-03 – Licencia fuera del umbral de vencimiento no genera alerta
"""
import pytest
from conftest import (
    configure_alerts, create_license, delete_license_by_name,
    run_expiring_alerts, today_plus,
)


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu05_01_licencia_dentro_30_dias(alerts_enabled, lic_registry):
    """
    Verifica que snipeit:expiring-alerts detecta y reporta una licencia cuya
    Expiration Date cae dentro de los próximos 30 días.
    Técnica: Caja negra / Partición de equivalencia – valor válido.
    """
    name = "LIC-HU05-01"
    lic_registry.append(name)
    delete_license_by_name(name)
    create_license(name, expiration_date=today_plus(12))

    output = run_expiring_alerts()

    assert name in output, (
        f"Se esperaba que '{name}' apareciera en el reporte de alertas.\n"
        f"Output del comando:\n{output}"
    )


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu05_02_licencia_exactamente_en_limite(alerts_enabled, lic_registry):
    """
    Verifica que una licencia cuya Expiration Date es exactamente hoy + 30 días
    (el borde superior del umbral) es incluida en las alertas.
    Técnica: Análisis de valores límite – límite superior inclusivo.

    Nota técnica: scopeExpiringLicenses() usa whereBetween(expiration_date,
    [Carbon::now(), Carbon::now()->addDays(30)]). Las fechas se almacenan como
    DATE en MySQL (sin hora), por lo que '2026-07-04 00:00:00' queda DENTRO del
    rango con Carbon::now()->addDays(30) = '2026-07-04 hh:mm:ss'. Confirmado
    en ejecución: LIC-HU05-02 aparece en el output.
    """
    name = "LIC-HU05-02"
    lic_registry.append(name)
    delete_license_by_name(name)
    create_license(name, expiration_date=today_plus(30))

    output = run_expiring_alerts()

    assert name in output, (
        f"El límite superior (día 30) debería ser inclusivo. "
        f"'{name}' no aparece en el output.\n{output}"
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu05_03_licencia_fuera_del_umbral(alerts_enabled, lic_registry):
    """
    Verifica que una licencia cuya Expiration Date es hoy + 45 días (fuera del
    umbral de 30 días) NO genera alerta.
    Técnica: Caja negra / Valor inválido (fuera de la partición).
    """
    name = "LIC-HU05-03"
    lic_registry.append(name)
    delete_license_by_name(name)
    create_license(name, expiration_date=today_plus(45))

    output = run_expiring_alerts()

    assert name not in output, (
        f"'{name}' (vence en 45 días) no debería aparecer en alertas de 30 días.\n"
        f"Output:\n{output}"
    )
