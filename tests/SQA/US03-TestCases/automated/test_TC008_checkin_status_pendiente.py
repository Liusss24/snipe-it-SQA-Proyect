"""
TC008 - Checkin con status no-deployable (Pending)
Tipo        : Sistema
Técnica     : Flujo completo con reclasificación de estado
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Usuario logueado con permisos de Checkin
  - Asset en estado "Deployed" asignado a un usuario registrado
  - Status Label "Pending" existe y es de tipo no-deployable

Pasos:
  1. Navegar a Assets → List All
  2. Click en el botón Checkin del asset Deployed
  3. Status: seleccionar "Pending"
  4. Notes: ingresar "Pantalla rota, enviado a reparación"
  5. Click en "Checkin Asset"
  6. Verificar mensaje de confirmación
  7. Navegar al detalle del asset
  8. Verificar que el botón Checkout está deshabilitado (status no-deployable)

Resultados esperados:
  - Mensaje: "Asset checked in successfully"
  - El botón Checkout aparece deshabilitado: el asset quedó con status Pending
    (no-deployable) y no puede volver a ser asignado hasta cambiar su status
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage

NOTES_TEXT   = "Pantalla rota, enviado a reparación"
STATUS_LABEL = "Pending"


@pytest.mark.checkout
class TestCheckinStatusPendiente:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, logged_in_driver, base_url, request):
        """Hace el checkin con status Pending UNA vez para toda la clase.

        scope="class" evita repetir el checkin en cada test, lo que dejaría
        el asset en Pending (no-deployable) impidiendo que el siguiente test
        encuentre un activo para hacer checkout previo.
        """
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip("No hay activos Deployed ni RTD disponibles; "
                            "precondición TC008 no cumplida.")

        page = CheckinPage(logged_in_driver, base_url)
        page.navigate_to_first_checkin(base_url)

        request.cls.asset_id = page.get_asset_id_from_url()
        page.select_status_by_name(STATUS_LABEL)
        page.set_notes(NOTES_TEXT)
        page.submit()

        request.cls.success_message = page.get_success_message()
        request.cls.page            = page
        request.cls.base_url        = base_url

    def test_checkin_exitoso(self):
        """El sistema debe confirmar el checkin aunque el status sea no-deployable."""
        assert "checked in" in self.success_message.lower(), \
            f"Mensaje de éxito inesperado. Se obtuvo: '{self.success_message}'"

    def test_checkout_deshabilitado(self):
        """El botón Checkout debe estar deshabilitado al quedar en status Pending."""
        assert self.asset_id is not None, \
            "No se pudo obtener el ID del asset desde la URL del checkin."

        self.page.navigate_to_asset_detail(self.asset_id)

        assert self.page.is_checkout_button_disabled(), \
            ("El botón Checkout no está deshabilitado; el status 'Pending' "
             "debería impedir el checkout del asset.")
