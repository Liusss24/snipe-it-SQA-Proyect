"""
TC019 - Checkin de asset con status "Out for Repair"
Tipo        : Sistema
Técnica     : Flujo completo con reclasificación de estado
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Usuario logueado con permisos de Checkin
  - Asset en estado "Deployed" asignado a un usuario registrado
  - Status Label "Out for Repair" existe y es de tipo Pending (no-deployable)

Pasos:
  1. Ir a Assets > List All
  2. Click en el botón Checkin del asset Deployed
  3. Status: seleccionar "Out for Repair"
  4. Notes: "Pantalla rota, enviado a reparación"
  5. Click en "Checkin Asset"
  6. Verificar checkin exitoso
  7. Verificar "Assigned To" vacío
  8. Verificar Status Label muestra "Out for Repair"
  9. Verificar botón Checkout deshabilitado (tipo Pending no permite deployment)
  10. Verificar que el historial registra el cambio de status

Resultados esperados:
  - Checkin exitoso: mensaje "Asset checked in successfully"
  - "Assigned To": vacío (asset ya no asignado)
  - Status Label: "Out for Repair" visible en el detalle
  - Botón Checkout deshabilitado (status no-deployable)
  - Historial registra el evento de checkin
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage
from pages.user_page import UserPage

NOTES_TEXT   = "Pantalla rota, enviado a reparación"
STATUS_LABEL = "Out for Repair"


@pytest.mark.checkout
class TestOutForRepair:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, logged_in_driver, base_url, request):
        """Realiza el checkin con status 'Out for Repair' una sola vez para toda la clase."""
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip(
                    "No hay assets Deployed ni RTD disponibles; "
                    "precondición TC019 no cumplida."
                )

        page      = CheckinPage(logged_in_driver, base_url)
        user_page = UserPage(logged_in_driver, base_url)

        page.navigate_to_first_checkin(base_url)
        asset_id = page.get_asset_id_from_url()

        page.select_status_by_name(STATUS_LABEL)
        page.set_notes(NOTES_TEXT)
        page.submit()

        request.cls.asset_id       = asset_id
        request.cls.success_message = page.get_success_message()
        request.cls.page           = page
        request.cls.user_page      = user_page
        request.cls.base_url       = base_url
        request.cls.driver         = logged_in_driver

    # ------------------------------------------------------------------

    def test_checkin_exitoso(self):
        """El sistema debe confirmar el checkin con mensaje de éxito."""
        assert "checked in" in self.success_message.lower(), \
            f"Mensaje de éxito inesperado. Se obtuvo: '{self.success_message}'"

    def test_assigned_to_vacio(self):
        """El campo 'Assigned To' debe quedar vacío tras el checkin."""
        self.page.navigate_to_asset_detail(self.asset_id)

        assert self.user_page.is_assigned_to_empty(), \
            f"El campo 'Assigned To' del asset {self.asset_id} no quedó vacío " \
            "después del checkin con status 'Out for Repair'."

    def test_status_label_out_for_repair(self):
        """El Status Label del asset debe mostrar 'Out for Repair'.

        Snipe-IT renderiza el status en un <div class="well"> como un enlace
        <a href="/statuslabels/{id}">…</a>, no en una fila <td>Status</td>.
        Se busca dicho enlace y se verifica que su texto coincida con STATUS_LABEL.
        """
        self.page.navigate_to_asset_detail(self.asset_id)

        try:
            status_link = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//a[contains(@href, '/statuslabels/')]"
                ))
            )
            assert STATUS_LABEL.lower() in status_link.text.lower(), \
                f"Se esperaba status '{STATUS_LABEL}' pero el enlace muestra: '{status_link.text}'"
        except TimeoutException:
            pytest.fail(
                f"No se encontró el enlace de status label en el detalle del asset {self.asset_id}. "
                "Snipe-IT renderiza el status como <a href='/statuslabels/…'> dentro de un .well."
            )

    def test_checkout_deshabilitado(self):
        """El botón Checkout debe estar deshabilitado ('Out for Repair' es tipo Pending)."""
        self.page.navigate_to_asset_detail(self.asset_id)

        assert self.page.is_checkout_button_disabled(), \
            ("El botón Checkout no está deshabilitado; el status 'Out for Repair' "
             "(tipo Pending) debería impedir el checkout del asset.")

    def test_historial_registra_checkin(self):
        """El historial del asset debe registrar el evento de checkin."""
        self.page.navigate_to_asset_detail(self.asset_id)
        self.page.open_history_tab()

        assert self.page.history_has_checkin_record(), \
            f"No se encontró registro de 'checkin' en el historial del asset {self.asset_id}."
