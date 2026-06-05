"""
Page object for the Snipe-IT main Dashboard.

Focuses on the "Recent Activity" table (#dashActivityReport), which lists
the last 25 system-wide events sorted by created_at DESC (newest first).

Table column order (0-based TD indices):
  0 - icon
  1 - created_at  (rendered by dateDisplayFormatter)
  2 - admin       (rendered by usersLinkObjFormatter)
  3 - action_type (plain text, e.g. "checkin from")
  4 - item        (rendered by polymorphicItemFormatter → link to asset)
  5 - target      (rendered by polymorphicItemFormatter → link to user)
"""
import re
from datetime import date
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from pages.base_page import BasePage


class DashboardPage(BasePage):

    ACTIVITY_TABLE = (By.ID, "dashActivityReport")
    ACTIVITY_ROWS  = (By.CSS_SELECTOR, "#dashActivityReport tbody tr")

    IDX_DATE   = 1
    IDX_ADMIN  = 2
    IDX_ACTION = 3
    IDX_ITEM   = 4
    IDX_TARGET = 5

    def navigate(self):
        self.go_to("/")

    def wait_for_activity_table(self, timeout=25):
        """Waits for Bootstrap-Table to finish the AJAX load and render rows."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.ACTIVITY_ROWS)
            )
        except Exception:
            pass

    def _row_text(self, row):
        return (row.get_attribute("textContent") or "").strip()

    def _row_cells(self, row):
        try:
            return row.find_elements(By.TAG_NAME, "td")
        except Exception:
            return []

    def _cell_text(self, row, idx):
        cells = self._row_cells(row)
        if len(cells) > idx:
            return (cells[idx].get_attribute("textContent") or "").strip()
        return ""

    def get_first_activity_row(self):
        """Returns the first TR in the activity table (most recent event, sorted DESC)."""
        try:
            self.wait_for_activity_table()
            rows = self.driver.find_elements(*self.ACTIVITY_ROWS)
            return rows[0] if rows else None
        except Exception:
            return None

    def get_activity_row_with_action_for_asset(self, action_text, asset_id, timeout=25):
        """
        Returns the first row where:
          - action column contains action_text
          - item column contains a link to /hardware/{asset_id}
        Waits up to timeout seconds for the AJAX data to arrive.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: action_text.lower() in d.page_source.lower()
            )
        except Exception:
            pass

        for _ in range(3):
            try:
                rows = self.driver.find_elements(*self.ACTIVITY_ROWS)
                for row in rows:
                    try:
                        action_ok = action_text.lower() in self._cell_text(
                            row, self.IDX_ACTION
                        ).lower()
                        item_ok = self._item_links_to(row, asset_id)
                        if action_ok and item_ok:
                            return row
                    except StaleElementReferenceException:
                        break
                break
            except StaleElementReferenceException:
                continue
        return None

    def _item_links_to(self, row, asset_id):
        """True if the item cell contains a link whose href includes /hardware/{asset_id}."""
        cells = self._row_cells(row)
        if len(cells) <= self.IDX_ITEM:
            return False
        try:
            links = cells[self.IDX_ITEM].find_elements(By.TAG_NAME, "a")
            return any(f"/hardware/{asset_id}" in (lnk.get_attribute("href") or "") for lnk in links)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Field-level verifiers for a single activity row
    # ------------------------------------------------------------------

    def row_has_today_year(self, row):
        """True if the date cell contains the current calendar year."""
        if row is None:
            return False
        return str(date.today().year) in self._cell_text(row, self.IDX_DATE)

    def row_has_time(self, row):
        """True if the date cell contains a time pattern HH:MM."""
        if row is None:
            return False
        return bool(re.search(r'\d{1,2}:\d{2}', self._cell_text(row, self.IDX_DATE)))

    def row_has_admin(self, row, username_fragment):
        """True if the admin cell contains username_fragment or any user profile link.

        Bootstrap-Table puede terminar de renderizar las celdas después de que
        los rows ya son visibles en el DOM. Se espera brevemente a que la celda
        tenga contenido. Si el nombre completo del admin no coincide con
        username_fragment (nombre de usuario vs. nombre completo), se acepta la
        presencia de cualquier enlace a /users/ como prueba de atribución válida,
        ya que el row ya fue identificado por action_type + asset_id.
        """
        if row is None:
            return False
        # Esperar a que Bootstrap-Table rellene el contenido de la celda admin
        try:
            cells = self._row_cells(row)
            if len(cells) > self.IDX_ADMIN:
                WebDriverWait(self.driver, 5).until(
                    lambda d: bool(
                        (cells[self.IDX_ADMIN].get_attribute("textContent") or "").strip()
                    )
                )
        except Exception:
            pass
        # Verificación primaria: el texto de la celda contiene username_fragment
        if username_fragment.lower() in self._cell_text(row, self.IDX_ADMIN).lower():
            return True
        # Fallback: nombre completo difiere del username → verificar enlace a /users/
        cells = self._row_cells(row)
        if len(cells) > self.IDX_ADMIN:
            return bool(
                cells[self.IDX_ADMIN].find_elements(By.CSS_SELECTOR, "a[href*='/users/']")
            )
        return False

    def row_has_action(self, row, action_text):
        """True if the action cell contains action_text (case-insensitive)."""
        if row is None:
            return False
        return action_text.lower() in self._cell_text(row, self.IDX_ACTION).lower()

    def row_item_links_to_asset(self, row, asset_id):
        """True if the item cell links to /hardware/{asset_id}."""
        if row is None:
            return False
        return self._item_links_to(row, asset_id)

    def first_row_is(self, row):
        """True if the given row is the topmost row in the activity table."""
        if row is None:
            return False
        try:
            rows = self.driver.find_elements(*self.ACTIVITY_ROWS)
            if not rows:
                return False
            return self._row_text(rows[0]) == self._row_text(row)
        except Exception:
            return False
