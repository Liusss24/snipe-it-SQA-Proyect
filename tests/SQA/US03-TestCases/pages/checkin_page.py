import re
from datetime import date
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from pages.base_page import BasePage


class CheckinPage(BasePage):

    # En el listado
    CHECKIN_BUTTON  = (By.CSS_SELECTOR, "a.btn-checkin")

    # En el formulario de checkin
    STATUS_ARROW    = (By.CSS_SELECTOR, "span.select2-selection__arrow")
    NOTES_FIELD     = (By.NAME, "note")
    SUBMIT_BUTTON   = (By.ID, "submit_button")
    CANCEL_LINK     = (By.CSS_SELECTOR, "a.btn.btn-link")

    # Resultado
    SUCCESS_ALERT   = (By.CSS_SELECTOR, ".alert-success")
    ASSIGNED_TO     = (By.CSS_SELECTOR, ".assigned_to, [data-label='Assigned To']")

    # Historial — selector por atributo href exacto (independiente del idioma del label)
    HISTORY_TAB     = (By.CSS_SELECTOR, "a[href='#history']")
    HISTORY_ROW     = (By.CSS_SELECTOR, "#history table tbody tr")

    def navigate_to_first_checkin(self, base_url):
        """Navega al listado y hace click en el primer botón Checkin disponible."""
        self.go_to("/hardware")
        self.js_click(*self.CHECKIN_BUTTON)

    def select_status(self):
        """Abre el dropdown de Status y selecciona la primera opción disponible."""
        self.wait_for_clickable(*self.STATUS_ARROW).click()
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
        raise RuntimeError("No se pudo seleccionar Status en el checkin")

    def select_status_by_name(self, name):
        """Abre el dropdown de Status y selecciona la opción cuyo texto coincida con name.

        Lanza RuntimeError si el status no existe en el dropdown, sin seleccionar
        otro por defecto (evita seleccionar silenciosamente el status incorrecto).
        """
        self.wait_for_clickable(*self.STATUS_ARROW).click()
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".select2-results__option")
        ))
        for _ in range(5):
            try:
                results = self.driver.find_elements(
                    By.CSS_SELECTOR, ".select2-results__option:not(.loading-results)"
                )
                for result in results:
                    if name.lower() in result.text.lower():
                        result.click()
                        return
            except StaleElementReferenceException:
                continue
        available = [r.text for r in self.driver.find_elements(
            By.CSS_SELECTOR, ".select2-results__option"
        )]
        raise RuntimeError(
            f"Status '{name}' no encontrado en el dropdown. "
            f"Opciones disponibles: {available}"
        )

    def clear_notes(self):
        try:
            field = self.driver.find_element(*self.NOTES_FIELD)
            field.clear()
        except Exception:
            pass

    def set_notes(self, text):
        """Borra el campo Notes e ingresa el texto dado."""
        try:
            field = self.wait_for_clickable(*self.NOTES_FIELD)
            field.clear()
            field.send_keys(text)
        except Exception:
            pass

    def get_asset_id_from_url(self):
        """Extrae el ID del asset desde la URL del formulario de checkin."""
        url = self.driver.current_url.rstrip('/')
        parts = url.split('/')
        try:
            idx = parts.index('checkin')
            return int(parts[idx - 1])
        except (ValueError, IndexError):
            return None

    def get_asset_tag_from_form(self):
        """Extrae el asset_tag del h2.box-title en el formulario de checkin.

        El template renderiza: 'Asset Tag <asset_tag>', p.ej. 'Asset Tag LAP-001'.
        Se retorna solo la porción después del prefijo 'Asset Tag'.
        """
        try:
            h2 = self.wait_for_element(By.CSS_SELECTOR, "h2.box-title")
            text = h2.text.strip()
            prefix = "Asset Tag"
            if prefix in text:
                return text[text.index(prefix) + len(prefix):].strip()
            return text
        except Exception:
            return None

    def navigate_to_asset_detail(self, asset_id):
        """Navega a la página de detalle del asset dado."""
        self.go_to(f"/hardware/{asset_id}")

    def is_checkout_button_visible(self):
        """Devuelve True si el botón Checkout (activo o deshabilitado) es visible.

        Snipe-IT renderiza <a class="bg-maroon hidden-print"> cuando el status es
        deployable, y <button disabled class="bg-maroon hidden-print"> cuando no lo
        es. Ambos indican que el asset ya no está asignado a nadie.
        """
        try:
            self.wait_for_element(By.CSS_SELECTOR, ".bg-maroon.hidden-print")
            return True
        except Exception:
            return False

    def is_checkout_button_disabled(self):
        """Devuelve True si el botón Checkout existe pero está deshabilitado.

        Ocurre cuando el status del asset es no-deployable (ej. 'Out for Repair').
        Snipe-IT renderiza <button class="bg-maroon hidden-print disabled">.
        """
        try:
            self.wait_for_element(By.CSS_SELECTOR, ".bg-maroon.hidden-print.disabled")
            return True
        except Exception:
            return False

    def history_has_note(self, text):
        """Devuelve True si el texto de nota aparece tras cargar las filas del historial."""
        try:
            self.wait_for_element(*self.HISTORY_ROW)
            return text.lower() in self.driver.page_source.lower()
        except Exception:
            return False

    def history_has_today_date(self):
        """Devuelve True si la fecha de hoy aparece en el historial (tras carga AJAX)."""
        from datetime import date
        try:
            self.wait_for_element(*self.HISTORY_ROW)
        except Exception:
            return False
        today = date.today().strftime("%Y-%m-%d")
        return today in self.driver.page_source

    def submit(self):
        self.wait_for_clickable(*self.SUBMIT_BUTTON).click()

    def is_success(self):
        try:
            self.wait.until(EC.presence_of_element_located(self.SUCCESS_ALERT))
            return True
        except Exception:
            return False

    def get_success_message(self):
        try:
            return self.wait_for_element(*self.SUCCESS_ALERT).text
        except Exception:
            return ""

    def open_history_tab(self):
        try:
            self.js_click(*self.HISTORY_TAB)
        except Exception:
            pass

    def history_has_checkin_record(self):
        try:
            self.wait_for_element(*self.HISTORY_ROW)
            return "checkin" in self.driver.page_source.lower()
        except Exception:
            return False

    def _row_text(self, row):
        """Texto completo de la fila vía textContent (funciona durante transición CSS y AJAX)."""
        return (row.get_attribute("textContent") or "").strip()

    def _wait_for_text_in_history(self, text, timeout=20):
        """Espera hasta que el texto aparezca en el page_source (un solo request vs N get_attribute).

        Bootstrap-Table carga filas vía AJAX; usar page_source es más eficiente que
        iterar rows con get_attribute() en cada ciclo del WebDriverWait.
        """
        from selenium.webdriver.support.ui import WebDriverWait as _WDW
        try:
            _WDW(self.driver, timeout).until(
                lambda d: text.lower() in d.page_source.lower()
            )
        except Exception:
            pass

    def get_history_row_with_notes(self, notes_text):
        """Devuelve la fila cuyo textContent contiene el texto de notas dado.

        Estrategia:
        1. Esperar que el texto aparezca en page_source (único request por ciclo).
        2. Localizar la fila específica una sola vez (no hay polling de elementos).

        La tabla se ordena ASC por created_at; el checkin actual es la última fila,
        no la primera.  Buscar por notas únicas es robusto al orden de sort.
        """
        self._wait_for_text_in_history(notes_text)
        rows = self.driver.find_elements(*self.HISTORY_ROW)
        for row in rows:
            try:
                if notes_text.lower() in self._row_text(row).lower():
                    return row
            except Exception:
                continue
        return None

    def get_first_history_row(self):
        """Devuelve la primera fila del historial (la más antigua con sort ASC)."""
        try:
            self.wait_for_element(*self.HISTORY_ROW)
            rows = self.driver.find_elements(*self.HISTORY_ROW)
            return rows[0] if rows else None
        except Exception:
            return None

    def get_last_history_row(self):
        """Devuelve la última fila del historial (la más reciente con sort ASC)."""
        try:
            self.wait_for_element(*self.HISTORY_ROW)
            rows = self.driver.find_elements(*self.HISTORY_ROW)
            return rows[-1] if rows else None
        except Exception:
            return None

    def history_row_contains(self, row, text):
        """True si la fila dada contiene el texto (sin distinguir mayúsculas)."""
        if row is None:
            return False
        return text.lower() in self._row_text(row).lower()

    def history_row_has_today_year(self, row):
        """True si la fila contiene el año actual (robusto a distintos formatos de fecha)."""
        if row is None:
            return False
        return str(date.today().year) in self._row_text(row)

    def history_row_has_time(self, row):
        """True si la fila contiene una hora en formato HH:MM."""
        if row is None:
            return False
        return bool(re.search(r'\d{1,2}:\d{2}', self._row_text(row)))

    def cancel(self):
        """Hace click en el enlace Cancel del formulario de checkin."""
        self.wait_for_clickable(*self.CANCEL_LINK).click()

    def get_history_count(self):
        """Devuelve el número de filas en el historial (llama después de open_history_tab)."""
        from selenium.webdriver.support.ui import WebDriverWait as _WDW
        try:
            _WDW(self.driver, 8).until(
                lambda d: len(d.find_elements(*self.HISTORY_ROW)) > 0
                          or "no records" in d.page_source.lower()
            )
        except Exception:
            pass
        return len(self.driver.find_elements(*self.HISTORY_ROW))

    def is_still_deployed(self):
        """True si el enlace de Checkin existe en el detalle del asset (sigue asignado).

        En la página de detalle el botón Checkin es <a href=".../checkin">;
        la clase a.btn-checkin solo existe en el listado, no en el detalle.
        """
        from selenium.webdriver.support.ui import WebDriverWait as _WDW
        try:
            _WDW(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/checkin']"))
            )
            return True
        except Exception:
            return False

    # --- Métodos legacy (usados por TC006) ---

    def history_first_row_contains(self, text):
        return self.history_row_contains(self.get_first_history_row(), text)

    def history_first_row_has_today_date(self):
        return self.history_row_has_today_year(self.get_last_history_row())

    def history_first_row_has_time(self):
        return self.history_row_has_time(self.get_last_history_row())
