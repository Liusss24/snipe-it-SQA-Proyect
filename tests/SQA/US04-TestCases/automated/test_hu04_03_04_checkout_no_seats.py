"""
CP-HU04-03 – Licencia sin cupos no permite checkout
CP-HU04-04 – Intento forzado de checkout sin cupos muestra advertencia
"""
import pytest
from pages.license_detail_page import LicenseDetailPage
from pages.checkout_page import CheckoutPage


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu04_03_licencia_sin_cupos_no_permite_checkout(
    auth_page, base_url, license_0_seats
):
    """
    Verifica que una licencia con Available Seats = 0 no permita iniciar
    un checkout normal.
    Alineado con: CP-HU04-03 (Prueba negativa – validación de estado)
    """
    lic_id = license_0_seats["id"]
    detail = LicenseDetailPage(auth_page, base_url)

    detail.navigate(lic_id)
    seats = detail.get_available_seats()
    assert seats == "0", f"Precondition failed: expected 0 seats, got {seats}"

    # Checkout button must be absent or not enabled
    checkout_enabled = detail.checkout_button_is_enabled()
    assert not checkout_enabled, (
        "Checkout button should not be enabled when Available Seats = 0"
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu04_04_intento_forzado_sin_cupos_muestra_advertencia(
    auth_page, base_url, license_0_seats
):
    """
    Verifica que, aun intentando forzar el flujo de checkout para una licencia
    agotada, el sistema lo bloquee y muestre la advertencia correspondiente.
    Alineado con: CP-HU04-04 (Prueba negativa – intento forzado)
    """
    lic_id = license_0_seats["id"]
    checkout = CheckoutPage(auth_page, base_url)

    # Force navigation to the checkout URL directly
    checkout.navigate(lic_id)

    # The system must show a warning or redirect
    assert checkout.has_no_seats_warning(), (
        "Expected 'There are no available seats' warning when forcing checkout on exhausted license"
    )

    # Counters must not change (Available Seats stays at 0)
    from pages.license_detail_page import LicenseDetailPage
    detail = LicenseDetailPage(auth_page, base_url)
    detail.navigate(lic_id)
    seats = detail.get_available_seats()
    assert seats == "0", (
        f"Available Seats must remain 0 after failed forced checkout, got {seats}"
    )
