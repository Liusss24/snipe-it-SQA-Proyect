"""
CP-HU04-01 – Checkout exitoso con cupos disponibles
CP-HU04-02 – Checkout exitoso con último cupo disponible
"""
import pytest
from conftest import get_free_seats, get_checked_out_count
from pages.checkout_page import CheckoutPage
from pages.license_detail_page import LicenseDetailPage


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu04_01_checkout_exitoso_con_cupos_disponibles(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Valida que un gestor pueda asignar una licencia a un usuario cuando la
    licencia tiene más de un cupo disponible.
    Técnica: Partición de equivalencia – valor válido.
    """
    lic_id   = license_2_seats["id"]
    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    assert get_free_seats(lic_id) == 2, "Precondición: se esperaban 2 cupos libres"
    checked_out_before = get_checked_out_count(lic_id)

    detail.navigate_to_checkout(lic_id)
    assert checkout.is_checkout_form_visible(), "El formulario de checkout debe estar visible"

    checkout.select_user(user_juan["id"], user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower(), (
        f"Mensaje esperado 'checked out successfully', recibido: {flash!r}"
    )
    assert get_free_seats(lic_id) == 1, "Available Seats debe ser 1 tras el checkout"
    assert get_checked_out_count(lic_id) == checked_out_before + 1


@pytest.mark.sistema
@pytest.mark.high
def test_cp_hu04_02_checkout_exitoso_con_ultimo_cupo(
    auth_page, base_url, license_1_seat, user_juan
):
    """
    Verifica el comportamiento cuando se asigna el último cupo disponible.
    Técnica: Análisis de valores límite.
    """
    lic_id   = license_1_seat["id"]
    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)

    assert get_free_seats(lic_id) == 1, "Precondición: se esperaba exactamente 1 cupo"

    detail.navigate_to_checkout(lic_id)
    checkout.select_user(user_juan["id"], user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower(), (
        f"Mensaje esperado 'checked out successfully', recibido: {flash!r}"
    )
    assert get_free_seats(lic_id) == 0, "Available Seats debe ser 0 tras consumir el último cupo"

    # El formulario ya no debe ser accesible
    detail.navigate_to_checkout(lic_id)
    assert not checkout.is_checkout_form_visible(), (
        "El formulario de checkout no debe mostrarse cuando no quedan cupos"
    )
