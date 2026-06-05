"""
TC012 - Notes con caracteres especiales, acentos y símbolos
Tipo        : Sistema
Técnica     : Valores límite (caracteres especiales)
Ejecución   : Automatizada
Prioridad   : Media
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Asset en estado Deployed asignado a un usuario

Pasos:
  1. Login en Snipe-IT
  2. Click en botón Checkin del asset Deployed
  3. Seleccionar status Ready to Deploy
  4. Notes: ingresar cadena con acentos, símbolos y caracteres especiales
  5. Click en "Checkin Asset"
  6. Verificar mensaje de confirmación
  7. Verificar que no hay inyección de código en la página de resultado

Resultados esperados:
  - Checkin exitoso
  - No hay ejecución de código inyectado (XSS)
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage

# Cubre: acentos, eñe, símbolos ASCII, caracteres del krecorder e intento XSS
NOTES_TEXT   = "áéíóú Ñoño @#$%* ¿válido? --..../*/*/*/2580985 <b>no-html</b>"
STATUS_LABEL = "Ready to Deploy"


@pytest.mark.checkout
class TestNotesCaracteresEspeciales:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, logged_in_driver, base_url, request):
        """Hace el checkin con notas especiales UNA vez para toda la clase."""
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip("No hay activos Deployed ni RTD; "
                            "precondición TC012 no cumplida.")

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
        """El checkin debe completarse con caracteres especiales en Notes."""
        assert "checked in" in self.success_message.lower(), \
            f"Mensaje de éxito inesperado. Se obtuvo: '{self.success_message}'"

    def test_sin_inyeccion_de_codigo(self):
        """El contenido HTML en Notes debe aparecer escapado, no ejecutado."""
        assert self.asset_id is not None, \
            "No se pudo obtener el ID del asset."

        self.page.navigate_to_asset_detail(self.asset_id)

        source = self.page.driver.page_source

        # "<b>no-html</b>" debe aparecer escapado (&lt;b&gt;), nunca renderizado
        assert "<b>no-html</b>" not in source, \
            "La etiqueta <b> se renderizó como HTML real; posible vulnerabilidad XSS."
