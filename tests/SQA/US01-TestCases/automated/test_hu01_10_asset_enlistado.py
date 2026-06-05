"""
TC018 - Asset aparece en listado general inmediatamente tras creación exitosa
Tipo        : Sistema
Técnica     : Flujo completo de creación y verificación de listado
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Verifica que después de crear un asset exitosamente, este aparece de inmediato
en el listado general de Assets sin necesidad de refrescar manualmente.
Se usa un serial y tag únicos por ejecución para evitar conflictos con corridas anteriores.
"""
import pytest
import time
from pages.asset_create_page import AssetCreatePage
from pages.asset_list_page import AssetListPage


_TS          = int(time.time())
SERIAL_UNICO = f"SN-TC018-{_TS}"
ASSET_TAG    = f"TC018-{_TS}"


@pytest.mark.assets
class TestAssetEnlistado:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        self.create_page = AssetCreatePage(logged_in_driver, base_url)
        self.list_page   = AssetListPage(logged_in_driver, base_url)

    def test_asset_visible_en_listado_sin_refrescar(self):
        """
        Flujo completo:
          1. Anotar total de assets antes de crear.
          2. Crear asset con serial único.
          3. Verificar creación exitosa.
          4. Navegar a Assets > List All (sin refrescar manualmente).
          5. Buscar el asset por tag único y verificar que aparece.
          6. Verificar que el contador de assets incrementó en 1.
        """
        # 1. Ir a Assets > List All y contar assets actuales
        self.list_page.load()
        total_antes = self.list_page.get_total_count()

        # 2. Assets > Create New: crear asset con serial único
        self.create_page.load()
        self.create_page.set_asset_tag(ASSET_TAG)
        self.create_page.set_serial(SERIAL_UNICO)
        self.create_page.select_select2_by_id("select2-model_select_id-container")
        self.create_page.select_select2_by_id("select2-status_select_id-container")
        self.create_page.save()

        # 3. Verificar que el guardado fue exitoso
        assert self.create_page.is_success(), \
            f"El asset '{ASSET_TAG}' (serial: {SERIAL_UNICO}) no se guardó exitosamente."

        # 4. Sin refrescar página, navegar a Assets > List All
        self.list_page.load()
        total_despues = self.list_page.get_total_count()

        # 5. Buscar el asset por tag único y verificar que aparece de inmediato
        assert self.list_page.is_asset_visible(ASSET_TAG), \
            f"El asset '{ASSET_TAG}' (serial: {SERIAL_UNICO}) no aparece en el listado " \
            "después de crearlo sin refrescar manualmente."

        # 6. El contador de assets debe haber incrementado exactamente en 1
        assert total_despues == total_antes + 1, \
            f"Se esperaba {total_antes + 1} assets en el listado, " \
            f"pero se encontraron {total_despues}."
