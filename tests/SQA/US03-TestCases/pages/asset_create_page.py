from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from pages.base_page import BasePage


class AssetCreatePage(BasePage):

    ASSET_TAG_INPUT = (By.ID, "asset_tag")
    SERIAL_INPUT    = (By.XPATH, "//input[@id='serials[1]']")
    SAVE_BUTTON     = (By.NAME, "submit")
    SUCCESS_ALERT   = (By.CSS_SELECTOR, ".alert-success")
    TAG_ERROR       = (By.ID, "asset_tag-error")
    MODEL_ERROR     = (By.ID, "model_select_id-error")
    STATUS_ERROR    = (By.ID, "status_select_id-error")

    def load(self):
        self.go_to("/hardware/create")
        self.wait_for_clickable(*self.ASSET_TAG_INPUT)

    def set_asset_tag(self, value):
        field = self.wait_for_clickable(*self.ASSET_TAG_INPUT)
        field.clear()
        field.send_keys(value)

    def clear_asset_tag(self):
        field = self.wait_for_clickable(*self.ASSET_TAG_INPUT)
        field.clear()

    def set_serial(self, value):
        field = self.wait_for_clickable(*self.SERIAL_INPUT)
        field.clear()
        field.send_keys(value)

    def select_select2_by_id(self, container_id, search_text=""):
        """Abre un dropdown Select2 y selecciona la primera opción disponible.
        Re-busca el elemento en cada intento para evitar StaleElementReferenceException."""
        self.wait_for_clickable(By.ID, container_id).click()
        if search_text:
            search_box = self.wait_for_clickable(By.CSS_SELECTOR, ".select2-search__field")
            search_box.send_keys(search_text)
        # Espera a que carguen los resultados y reintenta si el DOM se actualiza
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".select2-results__option:not(.loading-results)")
        ))
        for _ in range(5):
            try:
                results = self.driver.find_elements(
                    By.CSS_SELECTOR, ".select2-results__option:not(.loading-results)"
                )
                if results:
                    results[0].click()
                    return
            except StaleElementReferenceException:
                continue
        raise RuntimeError(f"No se pudo seleccionar opción en el Select2: {container_id}")

    def save(self):
        self.driver.find_element(*self.SAVE_BUTTON).click()

    def is_success(self):
        """Snipe-IT redirige fuera de /hardware/create al guardar exitosamente,
        y muestra .alert-success en la página destino."""
        try:
            # Esperar que salga de la página de creación
            self.wait.until(lambda d: "hardware/create" not in d.current_url)
            # Verificar alerta de éxito en la página destino
            self.wait.until(EC.presence_of_element_located(self.SUCCESS_ALERT))
            return True
        except Exception:
            return False

    def is_on_create_page(self):
        return "hardware/create" in self.driver.current_url

    def get_tag_error_text(self):
        try:
            return self.wait_for_element(*self.TAG_ERROR).text
        except Exception:
            return None

    def get_model_error_text(self):
        try:
            return self.wait_for_element(*self.MODEL_ERROR).text
        except Exception:
            return None

    def get_status_error_text(self):
        try:
            return self.wait_for_element(*self.STATUS_ERROR).text
        except Exception:
            return None
