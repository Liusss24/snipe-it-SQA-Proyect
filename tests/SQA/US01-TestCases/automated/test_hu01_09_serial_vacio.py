"""
TC004 - Serial Number es campo opcional
Tipo        : Sistema
Técnica     : Partición de equivalencia (campo opcional vacío)
Ejecución   : Automatizada
Valor       : Válido
Prioridad   : Media
Encargado   : Mariana Acuña Rodríguez

Rediseño: Serial no es obligatorio en Snipe-IT.
Se verifica visualmente que el campo no está marcado como requerido,
sin hacer click en Save para no crear datos en la base de datos.
"""
import pytest
from selenium.webdriver.common.by import By
from pages.asset_create_page import AssetCreatePage


@pytest.mark.assets
class TestSerialOpcional:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        self.page = AssetCreatePage(logged_in_driver, base_url)
        self.page.load()

    def test_serial_no_tiene_atributo_required(self):
        """El campo Serial no debe tener el atributo 'required' en el HTML."""
        campo_serial = self.page.driver.find_element(By.XPATH, "//input[@id='serials[1]']")
        required_attr = campo_serial.get_attribute("required")

        assert required_attr is None, \
            "El campo Serial tiene el atributo 'required', lo cual indica que es obligatorio."

    def test_serial_no_tiene_borde_naranja(self):
        """El campo Serial no debe tener el indicador visual de campo obligatorio (borde naranja)."""
        campo_serial = self.page.driver.find_element(By.XPATH, "//input[@id='serials[1]']")
        clases = campo_serial.get_attribute("class") or ""

        assert "required" not in clases and "error" not in clases, \
            "El campo Serial tiene clases de validación requerida, pero debería ser opcional."

    def test_etiqueta_serial_sin_asterisco(self):
        """La etiqueta del campo Serial no debe tener marcador de campo obligatorio (*)."""
        label = self.page.driver.find_element(
            By.XPATH, "//label[contains(., 'Serial') or @for='serials[1]']"
        )
        assert "*" not in label.text and "required" not in (label.get_attribute("class") or ""), \
            "La etiqueta Serial muestra indicador de campo obligatorio."
