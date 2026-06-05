"""
TC007 - Checkin de activo con notas y verificación de desvinculación
Tipo        : Sistema
Técnica     : Flujo completo
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Usuario con sesión iniciada y permisos de Checkin
  - Existe al menos un asset en estado "Deployed" asignado a un usuario válido
  - Status Label "Ready to Deploy" existe en el sistema

Pasos:
  1. Navegar a Assets → List All
  2. Localizar asset con botón Checkin (estado Deployed, usuario asignado)
  3. Click en el botón Checkin
  4. Seleccionar Status "Ready to Deploy"
  5. Ingresar notas "Equipo devuelto en buen estado"
  6. Click en "Checkin Asset"
  7. Verificar mensaje de confirmación
  8. Navegar al detalle del asset
  9. Verificar que el campo Assigned To ya no muestra un usuario

Resultados esperados:
  - Mensaje: "Asset checked in successfully"
  - En el detalle del asset: el campo Assigned To está vacío (aparece el
    botón Checkout en lugar del botón Checkin)
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage

NOTES_TEXT   = "Equipo devuelto en buen estado"
STATUS_LABEL = "Ready to Deploy"


@pytest.mark.checkout
class TestCheckinConNotas:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        """Garantiza que haya un asset Deployed antes de cada test.

        Primero busca un asset ya Deployed. Si el test anterior ya lo devolvió
        (ahora está en RTD), hace el checkout para dejarlo Deployed de nuevo.
        """
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            # No hay Deployed: intentar checkout de un activo RTD
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip("No hay activos Deployed ni RTD disponibles; "
                            "precondición TC007 no cumplida.")

        self.page     = CheckinPage(logged_in_driver, base_url)
        self.base_url = base_url
        self.asset_id = None

    def _do_checkin(self):
        self.page.navigate_to_first_checkin(self.base_url)
        self.asset_id = self.page.get_asset_id_from_url()
        self.page.select_status_by_name(STATUS_LABEL)
        self.page.set_notes(NOTES_TEXT)
        self.page.submit()

    def test_mensaje_confirmacion_correcto(self):
        """El sistema debe mostrar 'Asset checked in successfully' tras el checkin."""
        self._do_checkin()

        mensaje = self.page.get_success_message()
        assert "checked in" in mensaje.lower(), \
            f"Mensaje de éxito inesperado. Se obtuvo: '{mensaje}'"

    def test_asset_sin_usuario_asignado(self):
        """El campo Assigned To debe quedar vacío tras el checkin."""
        self._do_checkin()

        assert self.asset_id is not None, \
            "No se pudo obtener el ID del asset desde la URL del checkin."

        self.page.navigate_to_asset_detail(self.asset_id)

        assert self.page.is_checkout_button_visible(), \
            "El asset sigue mostrando un usuario asignado; el checkin no desvinculó al usuario."
