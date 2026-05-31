"""
CP-HU04-03 - Licencia sin cupos no permite checkout
CP-HU04-04 - Intento forzado de checkout sin cupos muestra advertencia

NOTA DE HALLAZGO (CP-HU04-03 / CP-HU04-14):
El campo available_actions.checkout de la API de Snipe-IT devuelve True para un
usuario administrador independientemente de si quedan cupos disponibles. El control
de disponibilidad de cupos se aplica en la capa de presentacion (UI) y en el
servidor al intentar el checkout, no como flag previo en el JSON de la licencia.
Esto puede ser un gap de documentacion o un comportamiento intencional para admins.
"""
import pytest
from conftest import get_free_seats
from pages.checkout_page import CheckoutPage
from pages.license_detail_page import LicenseDetailPage


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu04_03_licencia_sin_cupos_no_permite_checkout(
    auth_page, base_url, license_0_seats
):
    """
    Verifica que una licencia con Available Seats = 0 no permita iniciar
    un checkout normal.
    Tecnica: Prueba negativa - validacion de estado.
    """
    lic_id   = license_0_seats["id"]
    checkout = CheckoutPage(auth_page, base_url)

    # Verificar via API que efectivamente no hay cupos libres
    assert get_free_seats(lic_id) == 0, "Precondicion: la licencia debe tener 0 cupos"

    # UI: navegar al formulario de checkout; no debe mostrar el formulario
    checkout.navigate(lic_id)
    form_visible = checkout.is_checkout_form_visible()
    has_warning  = checkout.has_no_seats_warning()

    assert not form_visible or has_warning, (
        "Con 0 cupos disponibles, el sistema debe ocultar el formulario de "
        "checkout o mostrar una advertencia de 'no available seats'."
    )


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.medium
def test_cp_hu04_04_intento_forzado_sin_cupos_muestra_advertencia(
    auth_page, base_url, license_0_seats
):
    """
    Verifica que, al forzar la URL de checkout de una licencia agotada,
    el sistema lo bloquee y muestre la advertencia correspondiente.
    Tecnica: Prueba negativa - intento forzado via URL directa.
    """
    lic_id       = license_0_seats["id"]
    checkout     = CheckoutPage(auth_page, base_url)
    seats_before = get_free_seats(lic_id)

    # Forzar acceso a la URL de checkout directamente
    checkout.navigate(lic_id)

    form_shown   = checkout.is_checkout_form_visible()
    has_warning  = checkout.has_no_seats_warning()
    is_redirected = "/checkout" not in auth_page.url

    assert (not form_shown) or has_warning or is_redirected, (
        "El sistema debe bloquear el checkout forzado: el formulario no debe "
        "mostrarse y/o debe aparecer una advertencia de 'no available seats'."
    )

    # Los contadores no deben cambiar
    assert get_free_seats(lic_id) == seats_before, (
        "Available Seats no debe cambiar tras un intento fallido"
    )
