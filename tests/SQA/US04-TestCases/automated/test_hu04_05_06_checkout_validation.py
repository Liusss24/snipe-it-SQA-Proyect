"""
CP-HU04-05 – Validación del campo obligatorio "Checkout to" vacío
CP-HU04-06 – Cancelación del checkout antes de confirmar
"""
import pytest
from pages.license_detail_page import LicenseDetailPage
from pages.checkout_page import CheckoutPage


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu04_05_campo_checkout_to_vacio(
    auth_page, base_url, license_2_seats
):
    """
    Verifica que no se pueda confirmar el checkout sin seleccionar un usuario
    destino.
    Alineado con: CP-HU04-05 (Partición de equivalencia – campo obligatorio vacío)
    """
    lic_id = license_2_seats["id"]
    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    seats_before = None
    detail.navigate(lic_id)
    seats_before = detail.get_available_seats()

    # Open checkout form but leave "Checkout to" empty
    detail.click_checkout()
    checkout.submit()  # Submit without selecting a user

    # The system must not show a success message
    flash = checkout.get_flash_message()
    assert "checked out successfully" not in flash.lower(), (
        "System must not complete checkout when 'Checkout to' is empty"
    )

    # Validation errors must be present
    errors = checkout.get_validation_errors()
    assert len(errors) > 0, "Expected at least one validation error for empty 'Checkout to'"

    # Available Seats must not change
    detail.navigate(lic_id)
    seats_after = detail.get_available_seats()
    assert seats_after == seats_before, (
        f"Available Seats must not change after failed checkout (before={seats_before}, after={seats_after})"
    )


@pytest.mark.sistema
@pytest.mark.medium
def test_cp_hu04_06_cancelacion_checkout_no_genera_asignacion(
    auth_page, base_url, license_2_seats
):
    """
    Verifica que cancelar el formulario de checkout no genere asignación
    ni cambios en los contadores.
    Alineado con: CP-HU04-06 (Caja negra – validación de cancelación)
    """
    lic_id = license_2_seats["id"]
    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    detail.navigate(lic_id)
    seats_before = detail.get_available_seats()
    checked_out_before = detail.get_checked_out_count()

    # Open checkout form and cancel without confirming
    detail.click_checkout()
    checkout.cancel()

    # No success message should be visible
    flash = detail.get_flash_message()
    assert "checked out successfully" not in flash.lower(), (
        "A cancelled checkout must not produce a success message"
    )

    # Counters must remain unchanged
    detail.navigate(lic_id)
    seats_after = detail.get_available_seats()
    checked_out_after = detail.get_checked_out_count()

    assert seats_after == seats_before, (
        f"Available Seats must not change after cancellation (before={seats_before}, after={seats_after})"
    )
    assert checked_out_after == checked_out_before, (
        f"Checked Out must not change after cancellation (before={checked_out_before}, after={checked_out_after})"
    )
