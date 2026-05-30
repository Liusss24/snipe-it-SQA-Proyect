"""
CP-HU04-09 – Persistencia visual de contadores tras refrescar la página
CP-HU04-10 – Prevención de doble envío del checkout
"""
import pytest
from pages.license_detail_page import LicenseDetailPage
from pages.checkout_page import CheckoutPage


@pytest.mark.sistema
@pytest.mark.medium
def test_cp_hu04_09_persistencia_contadores_tras_refrescar(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Verifica que, después de un checkout exitoso, la información visible de
    la licencia se mantenga al refrescar la página.
    Alineado con: CP-HU04-09 (Caja negra – consistencia entre módulos)
    """
    lic_id = license_2_seats["id"]
    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    # Perform checkout
    detail.navigate(lic_id)
    detail.click_checkout()
    checkout.select_user("Juan Pérez")
    checkout.submit()

    # Record counters immediately after checkout
    detail.navigate(lic_id)
    seats_after = detail.get_available_seats()
    checked_out_after = detail.get_checked_out_count()

    assert seats_after == "1", f"Expected 1 after checkout, got {seats_after}"

    # Reload and verify values persist
    auth_page.reload()
    auth_page.wait_for_load_state("load")

    seats_after_reload = detail.get_available_seats()
    checked_out_after_reload = detail.get_checked_out_count()

    assert seats_after_reload == seats_after, (
        f"Available Seats changed after page reload: {seats_after} → {seats_after_reload}"
    )
    assert checked_out_after_reload == checked_out_after, (
        f"Checked Out changed after page reload: {checked_out_after} → {checked_out_after_reload}"
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu04_10_prevencion_doble_envio_checkout(
    auth_page, base_url, license_1_seat, user_juan
):
    """
    Verifica que un doble clic rápido sobre 'Checkout License' no genere una
    doble asignación visual ni un cambio doble de contadores.
    Alineado con: CP-HU04-10 (Prueba negativa – integridad de datos)
    """
    lic_id = license_1_seat["id"]
    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    detail.navigate(lic_id)
    seats_before = detail.get_available_seats()
    assert seats_before == "1", f"Precondition failed: expected 1 seat, got {seats_before}"

    # Open checkout and double-click submit
    detail.click_checkout()
    checkout.select_user("Juan Pérez")
    checkout.double_click_submit()

    # Only one success message should appear
    flash = detail.get_flash_message()
    success_count = flash.lower().count("checked out successfully")
    assert success_count <= 1, (
        f"Expected at most one success message, found {success_count}: {flash!r}"
    )

    # Available Seats must decrease exactly once (to 0, not below)
    detail.navigate(lic_id)
    seats_after = detail.get_available_seats()
    assert seats_after == "0", (
        f"Expected Available Seats = 0 (single decrement), got {seats_after}"
    )
    assert int(seats_after) >= 0, "Available Seats must not go below 0"
