"""
TC014 - Cancelar operación de checkin
Tipo        : Sistema
Técnica     : Flujo de cancelación
Ejecución   : Automatizada
Prioridad   : Media
Encargado   : Mariana Acuña Rodríguez

Precondición: Debe existir al menos un asset en estado "Deployed"
              asignado a un usuario en Snipe-IT antes de correr este test.

Pasos:
  1. Navegar a Assets → List All
  2. Localizar asset con botón Checkin (estado Deployed, usuario asignado)
  3. Click en el botón Checkin
  4. Llenar campo Notes
  5. Click en "Cancel"
  6. Verificar que no se realizó ningún checkin

Resultados esperados:
  - La URL regresa al listado de assets (no contiene /checkin)
  - El asset mantiene estado "Deployed" (botón Checkin sigue visible)
  - El asset sigue asignado al usuario original (no aparece botón Checkout)
  - No se agrega ningún registro nuevo al historial del asset
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage

NOTES_TEXT = "Nota de prueba cancelar"


@pytest.mark.checkout
class TestCancelarCheckin:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        """Garantiza que haya un asset Deployed antes de cada test."""
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip("No hay activos Deployed disponibles; precondición TC014 no cumplida.")

        self.page = CheckinPage(logged_in_driver, base_url)
        self.base_url = base_url

    def _do_cancel(self):
        """Navega al formulario de checkin, llena Notes y cancela. Devuelve el ID del asset."""
        self.page.navigate_to_first_checkin(self.base_url)
        asset_id = self.page.get_asset_id_from_url()
        self.page.set_notes(NOTES_TEXT)
        self.page.cancel()
        return asset_id

    def test_modal_cierra_sin_guardar(self):
        """Al cancelar, la URL debe abandonar /checkin y regresar al listado de assets."""
        self._do_cancel()

        current_url = self.page.driver.current_url
        assert "/checkin" not in current_url, \
            f"La URL sigue en la página de checkin tras cancelar: '{current_url}'"
        assert "/hardware" in current_url, \
            f"No se redirigió al listado de assets tras cancelar. URL actual: '{current_url}'"

    def test_asset_mantiene_estado_deployed(self):
        """El asset debe seguir en estado Deployed (botón Checkin visible) tras cancelar."""
        asset_id = self._do_cancel()

        self.page.navigate_to_asset_detail(asset_id)

        assert self.page.is_still_deployed(), \
            "El asset ya no muestra el botón Checkin; el estado Deployed pudo haberse perdido."

    def test_asset_sigue_asignado_usuario_original(self):
        """El asset no debe mostrar el botón Checkout tras cancelar; sigue asignado al usuario."""
        asset_id = self._do_cancel()

        self.page.navigate_to_asset_detail(asset_id)

        assert not self.page.is_checkout_button_visible(), \
            "El botón Checkout está visible, lo que indica que el asset fue desvinculado del usuario."

    def test_no_hay_registro_en_history(self):
        """El historial del asset no debe tener entradas nuevas tras cancelar el checkin."""
        self.page.navigate_to_first_checkin(self.base_url)
        asset_id = self.page.get_asset_id_from_url()

        # Contar entradas de historial antes de cancelar
        self.page.navigate_to_asset_detail(asset_id)
        self.page.open_history_tab()
        count_before = self.page.get_history_count()

        # Cancelar el checkin navegando directamente al formulario
        self.page.driver.get(f"{self.base_url}/hardware/{asset_id}/checkin")
        self.page.set_notes(NOTES_TEXT)
        self.page.cancel()

        # Verificar que el historial no cambió
        self.page.navigate_to_asset_detail(asset_id)
        self.page.open_history_tab()
        count_after = self.page.get_history_count()

        assert count_after == count_before, \
            f"El historial registró cambios tras cancelar: antes={count_before}, después={count_after}."
