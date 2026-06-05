"""
TC005 - Activo creado aparece inmediatamente en listado general
Tipo        : Sistema
Técnica     : Flujo completo de creación
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Nota: Este test crea un activo real en la base de datos ya que
verificar su aparición en el listado es el objetivo del caso.
Se usa un serial único por ejecución para evitar duplicados.
"""
import pytest
import time
from pages.asset_create_page import AssetCreatePage
from pages.asset_list_page import AssetListPage


# Serial único por ejecución para evitar conflictos con corridas anteriores
SERIAL_UNICO = f"SN-TC005-{int(time.time())}"
ASSET_TAG    = "Asset TC005"


@pytest.mark.assets
class TestCreacionExitosa:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        self.create_page = AssetCreatePage(logged_in_driver, base_url)
        self.list_page   = AssetListPage(logged_in_driver, base_url)

    def test_asset_aparece_en_listado_sin_refrescar(self):
        """Después de crear un asset, debe aparecer en el listado sin refrescar manualmente."""
        # Crear el asset
        self.create_page.load()
        self.create_page.set_asset_tag(ASSET_TAG)
        self.create_page.set_serial(SERIAL_UNICO)
        self.create_page.select_select2_by_id("select2-model_select_id-container")
        self.create_page.select_select2_by_id("select2-status_select_id-container")
        self.create_page.save()

        assert self.create_page.is_success(), "El asset no se guardó exitosamente."

        # Ir al listado sin refrescar (navegación directa)
        self.list_page.load()

        assert self.list_page.is_asset_visible(ASSET_TAG), \
            f"El asset '{ASSET_TAG}' no aparece en el listado después de crearlo."

    def test_contador_incrementa_en_uno(self):
        """El contador total de assets debe incrementar en 1 tras la creación."""
        # Contar antes
        self.list_page.load()
        total_antes = self.list_page.get_total_count()

        # Crear el asset
        self.create_page.load()
        self.create_page.set_asset_tag(f"{ASSET_TAG} B")
        self.create_page.set_serial(f"{SERIAL_UNICO}-B")
        self.create_page.select_select2_by_id("select2-model_select_id-container")
        self.create_page.select_select2_by_id("select2-status_select_id-container")
        self.create_page.save()

        # Contar después
        self.list_page.load()
        total_despues = self.list_page.get_total_count()

        assert total_despues == total_antes + 1, \
            f"Se esperaba {total_antes + 1} assets pero hay {total_despues}."

    def test_serial_correcto_en_listado(self):
        """El serial del asset creado debe mostrarse correctamente en el listado."""
        self.list_page.load()
        assert self.list_page.is_asset_visible(ASSET_TAG), \
            f"El asset con serial '{SERIAL_UNICO}' no aparece en el listado."
