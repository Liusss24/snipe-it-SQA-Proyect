"""
TC010 - Asset "Ready to Deploy" no asignado no muestra Checkin
Tipo        : Sistema
Técnica     : Prueba negativa / Validación de estado
Ejecución   : Automatizada
Prioridad   : Media
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Asset con status "Ready to Deploy" no asignado a nadie

Pasos:
  1. Login en Snipe-IT
  2. Navegar a Assets → Ready to Deploy
  3. Observar opciones disponibles en la columna de acciones

Resultados esperados:
  - Botón "Checkin" no visible en la lista
  - Botón "Checkout" disponible (asset listo para asignar)
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

RTD_URL = "/hardware?status_type=RTD"


@pytest.mark.assets
class TestRTDSinCheckin:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        """Verifica que exista al menos un asset RTD antes de cada test."""
        logged_in_driver.get(f"{base_url}{RTD_URL}")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.btn-checkout, span.btn-checkout")
                )
            )
        except TimeoutException:
            pytest.skip("No hay assets en estado RTD; precondición TC010 no cumplida.")

        self.driver   = logged_in_driver
        self.base_url = base_url

    def test_checkin_no_visible(self):
        """Un asset RTD no asignado no debe mostrar el botón Checkin."""
        checkin_buttons = self.driver.find_elements(
            By.CSS_SELECTOR, "a.btn-checkin"
        )
        assert len(checkin_buttons) == 0, \
            "Se encontró un botón Checkin en la lista RTD; no debería estar presente."

    def test_checkout_disponible(self):
        """Un asset RTD debe tener el botón Checkout disponible para asignarlo."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkout"))
            )
        except TimeoutException:
            pytest.fail("No se encontró el botón Checkout activo en la lista RTD.")
