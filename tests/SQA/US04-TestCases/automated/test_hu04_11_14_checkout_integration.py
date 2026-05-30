"""
CP-HU04-11 – El checkout exitoso se refleja en el perfil del usuario
CP-HU04-12 – Un checkout bloqueado no se refleja en el perfil del usuario
CP-HU04-13 – Consistencia entre detalle y listado de licencias después del checkout
CP-HU04-14 – Consistencia del estado "No Seats Available" en distintas vistas
"""
import pytest
from pages.license_detail_page import LicenseDetailPage
from pages.license_list_page import LicenseListPage
from pages.checkout_page import CheckoutPage
from pages.user_profile_page import UserProfilePage


@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu04_11_checkout_se_refleja_en_perfil_usuario(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Verifica la integración entre el detalle de la licencia y el perfil del
    usuario: una asignación exitosa debe aparecer en la sección Licenses del perfil.
    Alineado con: CP-HU04-11 (Caja negra – consistencia entre módulos)
    """
    lic_id = license_2_seats["id"]
    lic_name = license_2_seats.get("name", "LIC-HU04-01")
    user_id = user_juan["id"]

    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)
    profile = UserProfilePage(auth_page, base_url)

    # Perform checkout
    detail.navigate(lic_id)
    detail.click_checkout()
    checkout.select_user("Juan Pérez")
    checkout.submit()

    flash = detail.get_flash_message()
    assert "checked out successfully" in flash.lower(), (
        f"Checkout did not succeed: {flash!r}"
    )

    # Navigate to user profile and check Licenses section
    profile.navigate(user_id)
    assert profile.license_is_listed(lic_name), (
        f"License '{lic_name}' not found in user profile Licenses section"
    )


@pytest.mark.integracion
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu04_12_checkout_bloqueado_no_aparece_en_perfil(
    auth_page, base_url, license_0_seats, user_ana
):
    """
    Verifica que, si el checkout es bloqueado por falta de cupos, no aparezca
    ninguna licencia nueva en el perfil del usuario destino.
    Alineado con: CP-HU04-12 (Prueba negativa – consistencia entre módulos)
    """
    lic_id = license_0_seats["id"]
    lic_name = license_0_seats.get("name", "LIC-HU04-03")
    user_id = user_ana["id"]

    checkout = CheckoutPage(auth_page, base_url)
    profile = UserProfilePage(auth_page, base_url)

    # Attempt forced checkout (0 seats)
    checkout.navigate(lic_id)
    assert checkout.has_no_seats_warning(), "Expected 'no available seats' warning"

    # Verify license NOT listed in user profile
    profile.navigate(user_id)
    assert not profile.license_is_listed(lic_name), (
        f"License '{lic_name}' incorrectly appeared in user profile after blocked checkout"
    )


@pytest.mark.integracion
@pytest.mark.medium
def test_cp_hu04_13_consistencia_detalle_y_listado_tras_checkout(
    auth_page, base_url, license_2_seats, user_juan
):
    """
    Verifica que los contadores visibles en la vista detalle y en el listado
    general de licencias sean consistentes después de una asignación exitosa.
    Alineado con: CP-HU04-13 (Caja negra – consistencia entre vistas)
    """
    lic_id = license_2_seats["id"]
    lic_name = license_2_seats.get("name", "LIC-HU04-01")

    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)
    lic_list = LicenseListPage(auth_page, base_url)

    # Perform checkout
    detail.navigate(lic_id)
    detail.click_checkout()
    checkout.select_user("Juan Pérez")
    checkout.submit()

    # Record counters from detail view
    detail.navigate(lic_id)
    seats_detail = detail.get_available_seats()
    checked_out_detail = detail.get_checked_out_count()

    # Navigate to list view and compare
    lic_list.navigate()
    seats_list = lic_list.get_available_seats_for(lic_name)

    assert seats_list is not None, (
        f"License '{lic_name}' not found in list view"
    )
    assert seats_list == seats_detail, (
        f"Available Seats mismatch: detail={seats_detail}, list={seats_list}"
    )


@pytest.mark.integracion
@pytest.mark.high
def test_cp_hu04_14_consistencia_no_seats_en_distintas_vistas(
    auth_page, base_url, license_1_seat, user_juan
):
    """
    Verifica que, luego de consumir el último cupo, tanto el detalle como el
    listado general reflejan el estado de no disponibilidad.
    Alineado con: CP-HU04-14 (Caja negra – consistencia entre vistas)
    """
    lic_id = license_1_seat["id"]
    lic_name = license_1_seat.get("name", "LIC-HU04-02")

    detail = LicenseDetailPage(auth_page, base_url)
    checkout = CheckoutPage(auth_page, base_url)
    lic_list = LicenseListPage(auth_page, base_url)

    # Exhaust the last seat
    detail.navigate(lic_id)
    detail.click_checkout()
    checkout.select_user("Juan Pérez")
    checkout.submit()

    # Detail view: Available Seats = 0, Checkout disabled
    detail.navigate(lic_id)
    seats_detail = detail.get_available_seats()
    assert seats_detail == "0", f"Expected 0 seats in detail view, got {seats_detail}"
    assert not detail.checkout_button_is_enabled(), (
        "Checkout button should be disabled/hidden in detail view after last seat consumed"
    )

    # List view: Available Seats also = 0
    lic_list.navigate()
    seats_list = lic_list.get_available_seats_for(lic_name)
    assert seats_list == "0", (
        f"Expected 0 seats in list view, got {seats_list}"
    )
