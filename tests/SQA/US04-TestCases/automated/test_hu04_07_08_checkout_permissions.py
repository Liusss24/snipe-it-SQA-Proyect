"""
CP-HU04-07 – Usuario sin permisos no puede hacer checkout
CP-HU04-08 – Usuario no autenticado no puede acceder al flujo de checkout
"""
import pytest
from pages.checkout_page import CheckoutPage


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu04_07_usuario_sin_permisos_no_puede_hacer_checkout(
    noperm_page, base_url, license_2_seats
):
    """
    Verifica que un usuario sin permisos de gestión de licencias no pueda
    acceder ni ejecutar la acción de checkout.
    Alineado con: CP-HU04-07 (Control de permisos – prueba negativa)
    """
    lic_id = license_2_seats["id"]
    checkout = CheckoutPage(noperm_page, base_url)

    # Attempt direct navigation to checkout URL
    checkout.navigate(lic_id)
    current_url = noperm_page.url

    # System must redirect to login or show an access-denied page
    is_redirected = (
        "/login" in current_url
        or "/403" in current_url
        or "unauthorized" in noperm_page.content().lower()
        or "access denied" in noperm_page.content().lower()
        or "permission" in noperm_page.content().lower()
    )
    assert is_redirected, (
        f"User without permissions reached the checkout page. URL: {current_url}"
    )

    # No success confirmation must appear
    assert "checked out successfully" not in noperm_page.content().lower()


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu04_08_usuario_no_autenticado_no_puede_hacer_checkout(
    page, base_url, license_2_seats
):
    """
    Verifica que el flujo de checkout sólo pueda ejecutarse con sesión válida.
    Alineado con: CP-HU04-08 (Control de permisos – sin autenticación)
    """
    lic_id = license_2_seats["id"]
    checkout = CheckoutPage(page, base_url)

    # Navigate to checkout URL without any prior login
    checkout.navigate(lic_id)
    current_url = page.url

    # Must be redirected to login
    assert "/login" in current_url, (
        f"Unauthenticated user was not redirected to /login. Current URL: {current_url}"
    )
    assert "checked out successfully" not in page.content().lower()
