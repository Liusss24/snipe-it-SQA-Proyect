"""
CP-HU04-09 – Persistencia visual de contadores tras refrescar la página
CP-HU04-10 – Prevención de doble envío del checkout
"""
import pytest
from conftest import get_free_seats, get_checked_out_count
from pages.checkout_page import CheckoutPage
from pages.license_detail_page import LicenseDetailPage


@pytest.mark.sistema
@pytest.mark.medium
def test_cp_hu04_09_persistencia_contadores_tras_refrescar(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Verifica que los datos de la licencia se mantengan al refrescar tras checkout.
    Tecnica: Caja negra - persistencia de estado.
    """
    lic_id   = license_2_seats["id"]
    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    detail.navigate_to_checkout(lic_id)
    checkout.select_user(user_juan["id"], user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower(), f"Checkout previo fallido: {flash!r}"

    seats_after = get_free_seats(lic_id)
    co_after    = get_checked_out_count(lic_id)
    assert seats_after == 1

    # Refrescar y verificar persistencia
    detail.navigate(lic_id)
    assert get_free_seats(lic_id) == seats_after,     "Available Seats cambio tras refrescar"
    assert get_checked_out_count(lic_id) == co_after, "Checked Out cambio tras refrescar"


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu04_10_prevencion_doble_envio_checkout(
    auth_page, base_url, license_1_seat, user_juan
):
    """
    Verifica que al intentar hacer checkout dos veces seguidas (doble envio
    accidental), el sistema procese solo una asignacion y bloquee la segunda.
    Tecnica: Prueba negativa - integridad de datos.
    """
    lic_id   = license_1_seat["id"]
    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    assert get_free_seats(lic_id) == 1, "Precondicion: 1 cupo disponible"

    # Primer intento: debe tener exito
    detail.navigate_to_checkout(lic_id)
    checkout.select_user(user_juan["id"], user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash_1 = detail.get_flash_message()
    assert "checked out successfully" in flash_1.lower(), (
        f"El primer checkout debe ser exitoso. Flash: {flash_1!r}"
    )
    assert get_free_seats(lic_id) == 0, "Despues del primer checkout debe quedar 0 cupos"

    # Segundo intento inmediato: debe ser bloqueado (0 cupos)
    detail.navigate_to_checkout(lic_id)
    second_form_visible = checkout.is_checkout_form_visible()
    second_warning      = checkout.has_no_seats_warning()

    assert (not second_form_visible) or second_warning, (
        "El segundo intento debe ser bloqueado cuando no hay cupos disponibles"
    )

    # Los contadores no deben haber cambiado negativamente
    free_final = get_free_seats(lic_id)
    co_final   = get_checked_out_count(lic_id)
    assert free_final == 0,  "Available Seats no debe bajar de 0"
    assert free_final >= 0,  "Available Seats no puede ser negativo"
    assert co_final == 1,    f"Checked Out debe ser exactamente 1, got {co_final}"
