"""
CP-HU04-01 – Checkout exitoso con cupos disponibles
CP-HU04-02 – Checkout exitoso con último cupo disponible
"""
import pytest
from pages.license_detail_page import LicenseDetailPage
from pages.checkout_page import CheckoutPage


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu04_01_checkout_exitoso_con_cupos_disponibles(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Verifica que un gestor pueda asignar una licencia a un usuario cuando
    la licencia tiene más de un cupo disponible.
    Alineado con: CP-HU04-01 (Partición de equivalencia – valor válido)
    """
    lic_id = license_2_seats["id"]
    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    # Verify precondition: Available Seats = 2
    detail.navigate(lic_id)
    seats_before = detail.get_available_seats()
    assert seats_before == "2", f"Expected 2 available seats, got {seats_before}"

    # Perform checkout
    detail.click_checkout()
    checkout.select_user("Juan Pérez")
    checkout.submit()

    # Assert success message
    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower(), (
        f"Expected 'checked out successfully' in flash, got: {flash!r}"
    )

    # Assert Available Seats decreased
    detail.navigate(lic_id)
    seats_after = detail.get_available_seats()
    assert seats_after == "1", (
        f"Expected Available Seats = 1 after checkout, got {seats_after}"
    )


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu04_02_checkout_exitoso_con_ultimo_cupo(
    auth_page, base_url, license_1_seat, user_juan
):
    """
    Verifica el comportamiento del sistema cuando se asigna el último cupo
    disponible de una licencia.
    Alineado con: CP-HU04-02 (Análisis de valores límite)
    """
    lic_id = license_1_seat["id"]
    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    # Verify precondition: Available Seats = 1
    detail.navigate(lic_id)
    seats_before = detail.get_available_seats()
    assert seats_before == "1", f"Expected 1 available seat, got {seats_before}"

    # Perform checkout
    detail.click_checkout()
    checkout.select_user("Juan Pérez")
    checkout.submit()

    # Assert success message
    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower(), (
        f"Expected 'checked out successfully' in flash, got: {flash!r}"
    )

    # Assert Available Seats = 0
    detail.navigate(lic_id)
    seats_after = detail.get_available_seats()
    assert seats_after == "0", (
        f"Expected Available Seats = 0 after last checkout, got {seats_after}"
    )

    # Assert Checkout button is no longer accessible
    assert not detail.checkout_button_is_enabled(), (
        "Checkout button should be disabled/hidden when no seats remain"
    )
