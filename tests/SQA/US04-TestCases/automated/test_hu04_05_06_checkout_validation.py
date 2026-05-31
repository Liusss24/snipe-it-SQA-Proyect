"""
CP-HU04-05 – Validación del campo obligatorio "Checkout to" vacío
CP-HU04-06 – Cancelación del checkout antes de confirmar
"""
import pytest
from conftest import get_free_seats, get_checked_out_count
from pages.checkout_page import CheckoutPage
from pages.license_detail_page import LicenseDetailPage


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu04_05_campo_checkout_to_vacio(
    auth_page, base_url, license_2_seats
):
    """
    Verifica que no se pueda confirmar el checkout sin seleccionar un usuario.
    Técnica: Partición de equivalencia – campo obligatorio vacío.
    """
    lic_id       = license_2_seats["id"]
    checkout     = CheckoutPage(auth_page, base_url)
    seats_before = get_free_seats(lic_id)

    checkout.navigate(lic_id)
    assert checkout.is_checkout_form_visible()
    assert checkout.checkout_to_field_is_empty()

    checkout.submit()  # enviar sin usuario seleccionado

    # El sistema no debe confirmar el checkout
    flash = checkout.get_flash_message()
    assert "checked out successfully" not in flash.lower(), (
        "No debe mostrarse mensaje de éxito con 'Checkout to' vacío"
    )

    # Resultado esperado: o muestra error de validación, o muestra flash de error,
    # o el formulario permanece abierto. Cualquiera indica que el checkout fue rechazado.
    still_on_checkout = "/checkout" in auth_page.url
    has_errors        = len(checkout.get_validation_errors()) > 0
    has_error_flash   = flash != "" and "checked out" not in flash.lower()

    assert still_on_checkout or has_errors or has_error_flash, (
        f"El sistema debe rechazar el checkout sin usuario. "
        f"URL: {auth_page.url!r}, Flash: {flash!r}"
    )

    # Los contadores no deben haber cambiado
    assert get_free_seats(lic_id) == seats_before, (
        "Available Seats no debe cambiar si el checkout no se completó"
    )


@pytest.mark.sistema
@pytest.mark.medium
def test_cp_hu04_06_cancelacion_checkout_no_genera_asignacion(
    auth_page, base_url, license_2_seats
):
    """
    Verifica que cancelar el formulario no genere asignación ni cambie contadores.
    Técnica: Caja negra – validación de cancelación.
    """
    lic_id             = license_2_seats["id"]
    checkout           = CheckoutPage(auth_page, base_url)
    seats_before       = get_free_seats(lic_id)
    checked_out_before = get_checked_out_count(lic_id)

    checkout.navigate(lic_id)
    checkout.cancel()

    flash = checkout.get_flash_message()
    assert "checked out successfully" not in flash.lower()
    assert get_free_seats(lic_id) == seats_before
    assert get_checked_out_count(lic_id) == checked_out_before
