import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pages.base_page import BasePage


class UserPage(BasePage):

    # Listado de usuarios
    USERS_TABLE     = (By.CSS_SELECTOR, "table#table, table.table")
    USER_ROW        = (By.CSS_SELECTOR, "table tbody tr")

    # Detalle / perfil de usuario
    USER_HEADING    = (By.CSS_SELECTOR, "h1.pull-left, .page-header h1, h2.box-title")

    # Botón de eliminar — Snipe-IT usa un form DELETE o un enlace con data-method="DELETE"
    DELETE_BUTTON   = (By.CSS_SELECTOR, (
        "a[href*='/users/'][href$='/delete'], "
        "button[data-submit='delete-form'], "
        "form[action*='/users/'] button[type='submit']"
    ))
    DELETE_LINK     = (By.XPATH, "//a[contains(@href,'/delete') and "
                                  "(contains(translate(text(),'DELETE','delete'),'delete') "
                                  " or contains(@class,'delete') "
                                  " or contains(@data-toggle,'modal'))]")

    # Modal de confirmación de borrado
    CONFIRM_DELETE  = (By.CSS_SELECTOR,
                       "#dataConfirmModal .btn-danger, "
                       ".modal.in .btn-danger, "
                       "[data-confirm] .btn-confirm")

    # Alertas del sistema
    ALERT_ERROR     = (By.CSS_SELECTOR, ".alert-danger, .alert-warning")
    ALERT_SUCCESS   = (By.CSS_SELECTOR, ".alert-success")

    # Campo "Assigned To" en el detalle del asset
    # Snipe-IT renderiza filas de detalle como <td class="col-md-2">Assigned To</td> <td>…</td>
    ASSIGNED_TO_LABEL = (By.XPATH,
                          "//td[normalize-space(text())='Assigned To']"
                          "/following-sibling::td[1]")
    ASSIGNED_TO_LINK  = (By.XPATH,
                          "//td[normalize-space(text())='Assigned To']"
                          "/following-sibling::td[1]//a")

    def navigate_to_users(self):
        """Navega al listado de usuarios."""
        self.go_to("/users")

    def navigate_to_user(self, user_id):
        """Navega al perfil del usuario dado su ID."""
        self.go_to(f"/users/{user_id}")

    def get_assigned_user_id_from_asset_detail(self):
        """Extrae el ID de usuario del enlace 'Assigned To' en la página de detalle del asset.

        Snipe-IT renderiza: <a href="/users/{id}">Nombre del usuario</a>
        Retorna el ID como int, o None si el asset no está asignado.
        """
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(self.ASSIGNED_TO_LABEL)
            )
            link = self.driver.find_element(*self.ASSIGNED_TO_LINK)
            href = link.get_attribute("href") or ""
            match = re.search(r'/users/(\d+)', href)
            return int(match.group(1)) if match else None
        except (NoSuchElementException, TimeoutException):
            return None

    def get_assigned_user_name_from_asset_detail(self):
        """Obtiene el nombre del usuario asignado desde la página de detalle del asset."""
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(self.ASSIGNED_TO_LABEL)
            )
            cell = self.driver.find_element(*self.ASSIGNED_TO_LABEL)
            return cell.text.strip()
        except (NoSuchElementException, TimeoutException):
            return None

    def is_assigned_to_empty(self):
        """True si el campo 'Assigned To' está vacío (ningún enlace ni texto de usuario)."""
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(self.ASSIGNED_TO_LABEL)
            )
            cell = self.driver.find_element(*self.ASSIGNED_TO_LABEL)
            return cell.text.strip() == "" or cell.text.strip() == "—"
        except (NoSuchElementException, TimeoutException):
            return True

    def is_delete_blocked(self):
        """True si el botón de eliminar usuario NO está disponible o está deshabilitado.

        Snipe-IT bloquea el borrado de usuarios con assets asignados:
          - El enlace /delete puede estar ausente del toolbar
          - O estar presente pero marcado con 'disabled'
          - O inexistente porque isDeletable() devuelve false en el template
        """
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.DELETE_LINK)
            )
            btn = self.driver.find_element(*self.DELETE_LINK)
            classes = btn.get_attribute("class") or ""
            return "disabled" in classes
        except TimeoutException:
            return True

    def try_delete_user(self):
        """Intenta eliminar el usuario actual.

        Hace click en el botón/enlace de borrar y confirma el modal si aparece.
        Retorna True si se redirige con éxito (borrado ocurrió, inesperado),
        False si permanece en la página con un error (borrado bloqueado, esperado).
        """
        try:
            btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.DELETE_LINK)
            )
            btn.click()
        except TimeoutException:
            return False

        try:
            confirm = WebDriverWait(self.driver, 4).until(
                EC.element_to_be_clickable(self.CONFIRM_DELETE)
            )
            confirm.click()
        except TimeoutException:
            pass

        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.ALERT_ERROR)
            )
            return False
        except TimeoutException:
            pass

        return "users" in self.driver.current_url

    def get_error_message(self):
        """Retorna el texto del mensaje de error si está presente."""
        try:
            el = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.ALERT_ERROR)
            )
            return el.text.strip()
        except TimeoutException:
            return ""

    def user_still_exists(self, user_id):
        """True si la página del usuario (dado su ID) carga sin error 404/403."""
        self.navigate_to_user(user_id)
        source = self.driver.page_source.lower()
        return "not found" not in source and "404" not in source and "403" not in source
