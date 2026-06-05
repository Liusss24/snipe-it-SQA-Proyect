"""
TC009 - Devolución manteniendo status "Archived"
Tipo        : Sistema
Técnica     : Flujo completo con asset dado de baja
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Usuario logueado con permisos de Checkin
  - Asset con status "Archived" asignado a un usuario (Deployed)
  - Status Label "Archived" existe en el sistema

Pasos:
  1. Navegar a Assets → Archived
  2. Click en el botón Checkin del asset Archived+Deployed
  3. Status: seleccionar "Archived"
  4. Notes: ingresar "Equipo obsoleto devuelto"
  5. Click en "Checkin Asset"
  6. Verificar mensaje de confirmación
  7. Navegar al detalle del asset
  8. Verificar que el campo Assigned To está vacío
  9. Verificar que el botón Checkout está deshabilitado (asset dado de baja)

Resultados esperados:
  - Mensaje: "Asset checked in successfully"
  - Assigned To: vacío (asset desvinculado del usuario)
  - Status: "Archived" se mantiene
  - Botón Checkout deshabilitado: el asset dado de baja no puede ser asignado
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.checkin_page import CheckinPage

NOTES_TEXT   = "Equipo obsoleto devuelto"
STATUS_LABEL = "Archived"
ARCHIVED_URL = "/hardware?status_type=Archived"


@pytest.mark.checkout
class TestCheckinAssetArchivado:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, logged_in_driver, base_url, request):
        """Hace el checkin con status Archived UNA vez para toda la clase.

        Busca un asset Archived que esté Deployed (btn-checkin visible en la
        lista Archived). Si no existe, salta el test.
        """
        logged_in_driver.get(f"{base_url}{ARCHIVED_URL}")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            pytest.skip("No hay assets Archived+Deployed con botón Checkin; "
                        "precondición TC009 no cumplida.")

        page = CheckinPage(logged_in_driver, base_url)

        # Ya estamos en /hardware?status_type=Archived con btn-checkin visible.
        # No llamamos navigate_to_first_checkin porque ese método navega a
        # /hardware (lista general) donde los Archived pueden no aparecer.
        page.js_click(*CheckinPage.CHECKIN_BUTTON)

        request.cls.asset_id = page.get_asset_id_from_url()
        page.select_status_by_name(STATUS_LABEL)
        page.set_notes(NOTES_TEXT)
        page.submit()

        request.cls.success_message = page.get_success_message()
        request.cls.page            = page
        request.cls.base_url        = base_url

    def test_checkin_exitoso(self):
        """El checkin debe completarse aunque el status sea Archived."""
        assert "checked in" in self.success_message.lower(), \
            f"Mensaje de éxito inesperado. Se obtuvo: '{self.success_message}'"

    def test_asset_sin_usuario_asignado(self):
        """El campo Assigned To debe quedar vacío tras el checkin."""
        assert self.asset_id is not None, \
            "No se pudo obtener el ID del asset desde la URL del checkin."

        self.page.navigate_to_asset_detail(self.asset_id)

        assert self.page.is_checkout_button_visible(), \
            "El botón Checkout no aparece; el asset podría seguir asignado."

    def test_checkout_no_disponible(self):
        """El botón Checkout debe estar deshabilitado: asset dado de baja no es asignable."""
        assert self.asset_id is not None, \
            "No se pudo obtener el ID del asset desde la URL del checkin."

        self.page.navigate_to_asset_detail(self.asset_id)

        assert self.page.is_checkout_button_disabled(), \
            ("El botón Checkout no está deshabilitado; el status 'Archived' "
             "debería impedir cualquier asignación posterior.")
