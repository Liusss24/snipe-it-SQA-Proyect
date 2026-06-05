"""
CP-HU05-11 – Alertas deshabilitadas impiden envío de correo
CP-HU05-12 – Sin correo de alerta configurado no se envía notificación
CP-HU05-13 – Proceso programado diario ejecuta revisión de alertas
"""
import uuid
import pytest
from conftest import (
    configure_alerts, create_license, delete_license_by_name,
    run_artisan, run_expiring_alerts, today_plus,
)


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu05_11_alertas_deshabilitadas(alerts_disabled, lic_registry):
    """
    Verifica que cuando la opción 'Alerts Enabled' está desactivada, el comando
    snipeit:expiring-alerts no procesa ni notifica elementos aunque existan
    licencias próximas a vencer.
    Técnica: Caja negra / Configuración inválida.
    """
    name = f"LIC-HU05-11-{uuid.uuid4().hex[:6]}"
    lic_registry.append(name)
    create_license(name, expiration_date=today_plus(10))

    output = run_expiring_alerts()

    # El sistema debe indicar que las alertas están deshabilitadas
    assert "disabled" in output.lower(), (
        f"Se esperaba mensaje de alertas deshabilitadas. Output:\n{output}"
    )
    # Y no debe procesar la licencia creada
    assert name not in output, (
        f"'{name}' no debería aparecer cuando las alertas están deshabilitadas.\n{output}"
    )


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu05_12_sin_correo_configurado(alerts_no_email, lic_registry):
    """
    Verifica que el sistema no intenta enviar notificaciones si el campo de
    correo de alerta está vacío, manejando la situación sin errores no controlados.
    Técnica: Caja negra / Configuración inválida – campo requerido vacío.
    """
    name = f"LIC-HU05-12-{uuid.uuid4().hex[:6]}"
    lic_registry.append(name)
    create_license(name, expiration_date=today_plus(10))

    output = run_expiring_alerts()

    # El sistema debe informar que no hay correo configurado
    assert any(keyword in output.lower() for keyword in ["no alert email", "no mail", "no alert"]), (
        f"Se esperaba mensaje de correo no configurado. Output:\n{output}"
    )
    # La licencia no debería procesarse
    assert name not in output, (
        f"'{name}' no debería aparecer cuando no hay correo configurado.\n{output}"
    )


@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu05_13_scheduler_incluye_expiring_alerts(alerts_enabled):
    """
    Verifica que el scheduler de Laravel tiene registrado el comando
    snipeit:expiring-alerts con frecuencia diaria (cron '0 0 * * *').
    Técnica: Integración / Caja blanca parcial – inspección del scheduler.
    """
    output = run_artisan("schedule:list")

    assert "snipeit:expiring-alerts" in output, (
        f"El scheduler no incluye 'snipeit:expiring-alerts'.\n"
        f"Comandos programados:\n{output}"
    )
    # Verificar que está programado con frecuencia diaria
    assert "0    0 * * *" in output or "daily" in output.lower() or "0 0 * * *" in output, (
        f"'snipeit:expiring-alerts' no tiene frecuencia diaria en el scheduler.\n{output}"
    )
