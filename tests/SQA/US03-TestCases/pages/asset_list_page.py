import re
from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class AssetListPage(BasePage):

    TABLE       = (By.ID, "assetsListingTable")
    # DataTables genera el input de búsqueda con aria-controls apuntando al ID de la tabla
    SEARCH_BOX  = (By.CSS_SELECTOR, "input[aria-controls='assetsListingTable']")
    # El texto "Showing X to Y of Z" puede estar en varias clases según la versión de DataTables
    TABLE_INFO  = (By.CSS_SELECTOR, ".dataTables_info, [id$='_info']")

    def load(self):
        self.go_to("/hardware")
        self.wait_for_element(*self.TABLE)

    def search(self, text):
        box = self.wait_for_clickable(*self.SEARCH_BOX)
        box.clear()
        box.send_keys(text)
        # Espera a que DataTables termine de filtrar
        self.wait.until(lambda d: "processing" not in (
            d.find_element(*self.TABLE).get_attribute("class") or ""
        ))

    def get_total_count(self):
        """Extrae el total de assets del texto 'Showing X to Y of Z entries'."""
        info = self.wait_for_element(*self.TABLE_INFO).text
        match = re.search(r'of (\d+)', info)
        return int(match.group(1)) if match else 0

    def is_asset_visible(self, asset_tag):
        """Busca el asset_tag en la tabla y retorna True si aparece."""
        self.search(asset_tag)
        try:
            self.wait_for_element(
                By.XPATH,
                f"//table[@id='assetsListingTable']//a[contains(text(),'{asset_tag}')]"
            )
            return True
        except Exception:
            return False
