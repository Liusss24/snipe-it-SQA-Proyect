"""
CP-HU04-07 – Usuario sin permisos no puede hacer checkout
CP-HU04-08 – Usuario no autenticado no puede acceder al flujo de checkout
"""
import pytest
from conftest import get_free_seats
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
    Técnica: Control de permisos – prueba negativa.
    """
    lic_id       = license_2_seats["id"]
    checkout     = CheckoutPage(noperm_page, base_url)
    seats_before = get_free_seats(lic_id)

    # Intentar acceder directo a la URL de checkout
    checkout.navigate(lic_id)
    current_url  = noperm_page.url
    page_content = noperm_page.content().lower()

    is_blocked = (
        "/login"        in current_url
        or "/403"       in current_url
        or "unauthoriz" in page_content
        or "forbidden"  in page_content
        or "access deni" in page_content
        or "permission" in page_content
        or not checkout.is_checkout_form_visible()
    )
    assert is_blocked, (
        f"Usuario sin permisos llegó al formulario de checkout. URL actual: {current_url}"
    )

    # No debe aparecer confirmación de éxito
    assert "checked out successfully" not in page_content

    # Los cupos no deben cambiar
    assert get_free_seats(lic_id) == seats_before, (
        "Available Seats no debe modificarse tras un intento bloqueado por permisos"
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu04_08_usuario_no_autenticado_no_puede_hacer_checkout(
    page, base_url, license_2_seats
):
    """
    Verifica que el flujo de checkout sólo pueda ejecutarse con sesión válida.
    Técnica: Control de permisos – sin autenticación.
    """
    lic_id   = license_2_seats["id"]
    checkout = CheckoutPage(page, base_url)

    # Acceder sin login previo
    checkout.navigate(lic_id)
    current_url = page.url

    # Debe redirigir al login
    assert "/login" in current_url, (
        f"Usuario no autenticado debe ser redirigido a /login. URL actual: {current_url}"
    )
    assert "checked out successfully" not in page.content().lower()
