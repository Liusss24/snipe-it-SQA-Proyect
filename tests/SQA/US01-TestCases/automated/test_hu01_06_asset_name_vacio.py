"""
TC001 - Validación de campo obligatorio Asset Tag vacío
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
@pytest.mark.smoke
class TestAssetTagVacio:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        self.page = AssetCreatePage(logged_in_driver, base_url)
        self.page.load()

    def test_no_permite_guardar_sin_asset_tag(self):
        """El sistema no debe guardar el activo si Asset Tag está vacío."""
        self.page.clear_asset_tag()
        self.page.save()

        assert not self.page.is_success(), \
            "El sistema guardó el activo sin Asset Tag, lo cual no debería permitirse."

    def test_formulario_permanece_abierto(self):
        """El formulario no debe redirigir tras intentar guardar sin Asset Tag."""
        self.page.clear_asset_tag()
        self.page.save()

        assert self.page.is_on_create_page(), \
            "El sistema redirigió fuera del formulario a pesar del error de validación."

    def test_muestra_this_field_is_required(self):
        """Debe aparecer el mensaje 'This field is required' bajo el campo Asset Tag."""
        self.page.clear_asset_tag()
        self.page.save()

        error_text = self.page.get_tag_error_text()
        assert error_text is not None and len(error_text) > 0, \
            "No se mostró el mensaje de validación 'This field is required' para Asset Tag."
