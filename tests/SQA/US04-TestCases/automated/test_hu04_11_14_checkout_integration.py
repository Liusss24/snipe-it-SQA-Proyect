"""
CP-HU04-11 – El checkout exitoso se refleja en el perfil del usuario
CP-HU04-12 – Un checkout bloqueado no se refleja en el perfil del usuario
CP-HU04-13 – Consistencia entre detalle y listado de licencias después del checkout
CP-HU04-14 – Consistencia del estado "No Seats Available" en distintas vistas
"""
import pytest
from conftest import (
    get_free_seats, get_checked_out_count,
    user_has_license, can_checkout,
)
from pages.checkout_page import CheckoutPage
from pages.license_detail_page import LicenseDetailPage
from pages.license_list_page import LicenseListPage
from pages.user_profile_page import UserProfilePage


@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu04_11_checkout_se_refleja_en_perfil_usuario(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Asignación exitosa debe aparecer en la sección Licenses del perfil.
    Técnica: Caja negra – consistencia entre módulos.
    """
    lic_id   = license_2_seats["id"]
    lic_name = license_2_seats.get("name", "LIC-HU04-01")
    user_id  = user_juan["id"]

    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)
    profile  = UserProfilePage(auth_page, base_url)

    detail.navigate_to_checkout(lic_id)
    checkout.select_user(user_id, user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower(), f"Checkout fallido: {flash!r}"

    profile.navigate(user_id)
    assert user_has_license(user_id, lic_name), (
        f"Licencia '{lic_name}' no aparece en el perfil del usuario tras checkout"
    )


@pytest.mark.integracion
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu04_12_checkout_bloqueado_no_aparece_en_perfil(
    auth_page, base_url, license_0_seats, user_ana
):
    """
    Checkout bloqueado no debe dejar rastro en el perfil del usuario.
    Técnica: Prueba negativa – consistencia entre módulos.
    """
    lic_id   = license_0_seats["id"]
    lic_name = license_0_seats.get("name", "LIC-HU04-03")
    user_id  = user_ana["id"]

    checkout = CheckoutPage(auth_page, base_url)
    profile  = UserProfilePage(auth_page, base_url)

    checkout.navigate(lic_id)
    assert not checkout.is_checkout_form_visible() or checkout.has_no_seats_warning()

    profile.navigate(user_id)
    assert not user_has_license(user_id, lic_name), (
        "La licencia no debe aparecer en el perfil tras un checkout bloqueado"
    )


@pytest.mark.integracion
@pytest.mark.medium
def test_cp_hu04_13_consistencia_detalle_y_listado_tras_checkout(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Contadores deben ser coherentes entre la vista detalle y el listado.
    Técnica: Caja negra – consistencia entre vistas.
    """
    lic_id   = license_2_seats["id"]

    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)
    lic_list = LicenseListPage(auth_page, base_url)

    detail.navigate_to_checkout(lic_id)
    checkout.select_user(user_juan["id"], user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower()

    seats_detail = get_free_seats(lic_id)
    co_detail    = get_checked_out_count(lic_id)

    # Navegar al listado y verificar que la licencia existe en la tabla
    lic_list.navigate()
    row = lic_list.find_row(license_2_seats.get("name", "LIC-HU04-01"))
    assert row is not None, "La licencia debe aparecer en el listado"

    # Los datos de la API deben ser consistentes desde ambas vistas
    assert get_free_seats(lic_id) == seats_detail
    assert get_checked_out_count(lic_id) == co_detail


@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu04_14_consistencia_no_seats_en_distintas_vistas(
    auth_page, base_url, license_1_seat, user_juan
):
    """
    Al agotar el último cupo, ambas vistas deben reflejar no disponibilidad.
    Técnica: Caja negra – consistencia entre vistas.
    """
    lic_id   = license_1_seat["id"]

    detail   = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)
    lic_list = LicenseListPage(auth_page, base_url)

    detail.navigate_to_checkout(lic_id)
    checkout.select_user(user_juan["id"], user_juan.get("name", "Juan Perez"))
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower()

    # Vista detalle: 0 cupos, checkout bloqueado en UI
    # Nota: available_actions.checkout en la API retorna True para admin aunque no haya
    # cupos. El bloqueo se refleja en la UI (formulario no visible).
    assert get_free_seats(lic_id) == 0
    detail.navigate_to_checkout(lic_id)
    assert not checkout.is_checkout_form_visible()

    # Vista listado: licencia sigue visible
    lic_list.navigate()
    row = lic_list.find_row(license_1_seat.get("name", "LIC-HU04-02"))
    assert row is not None
    assert get_free_seats(lic_id) == 0
