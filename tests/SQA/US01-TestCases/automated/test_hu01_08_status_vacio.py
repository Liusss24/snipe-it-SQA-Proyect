"""
TC003 - Validación de campo obligatorio Status vacío
Tipo        : Sistema
Técnica     : Partición de equivalencia (campo vacío)
Ejecución   : Automatizada
Valor       : Inválido
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez
"""
import pytest
from pages.asset_create_page import AssetCreatePage


@pytest.mark.assets
class TestStatusVacio:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        self.page = AssetCreatePage(logged_in_driver, base_url)
        self.page.load()

    def test_no_permite_guardar_sin_status(self):
        """El sistema no debe guardar el activo si Status está vacío."""
        self.page.set_asset_tag("Laptop sin status")
        self.page.set_serial("SN-002")
        self.page.select_select2_by_id("select2-model_select_id-container")
        self.page.save()

        assert not self.page.is_success(), \
            "El sistema guardó el activo sin Status, lo cual no debería permitirse."

    def test_formulario_permanece_abierto(self):
        """El formulario no debe redirigir tras intentar guardar sin Status."""
        self.page.set_asset_tag("Laptop sin status")
        self.page.select_select2_by_id("select2-model_select_id-container")
        self.page.save()

        assert self.page.is_on_create_page(), \
            "El sistema redirigió fuera del formulario a pesar del error de validación."

    def test_muestra_validacion_status_requerido(self):
        """Debe aparecer mensaje de validación indicando que Status es obligatorio."""
        self.page.set_asset_tag("Laptop sin status")
        self.page.select_select2_by_id("select2-model_select_id-container")
        self.page.save()

        error_text = self.page.get_status_error_text()
        assert error_text is not None and len(error_text) > 0, \
            "No se mostró ningún mensaje de validación para el campo Status vacío."
