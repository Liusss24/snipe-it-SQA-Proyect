"""
TC002 - Validación de campo obligatorio Model vacío
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
class TestModelVacio:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        self.page = AssetCreatePage(logged_in_driver, base_url)
        self.page.load()

    def test_no_permite_guardar_sin_model(self):
        """El sistema no debe guardar el activo si Model está vacío."""
        self.page.set_asset_tag("Laptop Test")
        self.page.set_serial("SN-TEST-004")
        self.page.save()

        assert not self.page.is_success(), \
            "El sistema guardó el activo sin Model, lo cual no debería permitirse."

    def test_formulario_permanece_abierto(self):
        """El formulario no debe redirigir tras intentar guardar sin Model."""
        self.page.set_asset_tag("Laptop Test")
        self.page.save()

        assert self.page.is_on_create_page(), \
            "El sistema redirigió fuera del formulario a pesar del error de validación."

    def test_muestra_validacion_model_requerido(self):
        """Debe aparecer mensaje de validación indicando que Model es obligatorio."""
        self.page.set_asset_tag("Laptop Test")
        self.page.save()

        error_text = self.page.get_model_error_text()
        assert error_text is not None and len(error_text) > 0, \
            "No se mostró ningún mensaje de validación para el campo Model vacío."
