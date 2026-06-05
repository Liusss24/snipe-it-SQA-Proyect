"""
TC017 - Checkin de asset tras intento de eliminación del usuario asignado
Tipo        : Sistema / Edge Case
Técnica     : Análisis de valor límite · Manejo de casos borde
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Descripción:
  Verificar el comportamiento del sistema al intentar eliminar un usuario que
  tiene un asset asignado (estado Deployed), y confirmar que el sistema gestiona
  correctamente este edge case.

  NOTA DE DISEÑO: Snipe-IT impide eliminar usuarios con assets asignados mediante
  la validación en DeleteUserRequest (campo assigned_assets debe ser 0) y el método
  isDeletable() del modelo User. Por lo tanto:
    - El flujo "eliminar usuario y luego hacer checkin" NO puede ocurrir de forma
      normal en la UI.
    - Este test verifica que la PROTECCIÓN funciona correctamente (el sistema
      bloquea la eliminación) y que, una vez protegida la integridad, el checkin
      se puede realizar normalmente.

Precondiciones:
  - Usuario Admin con sesión iniciada y permisos de Checkin/Checkout/Manage Users
  - Existe al menos un asset en estado "Deployed" asignado a un usuario válido
    (o bien existe un asset RTD y un usuario disponible para hacer checkout)

Flujo del test:
  1. Garantizar un asset Deployed asignado a un usuario.
  2. Navegar al detalle del asset → obtener datos del usuario asignado.
  3. Navegar al perfil del usuario asignado.
  4. Verificar que el sistema BLOQUEA la eliminación (botón ausente/deshabilitado).
  5. Opcionalmente intentar la eliminación y verificar el mensaje de error.
  6. Navegar de vuelta al asset → realizar el checkin correctamente.
  7. Verificar: mensaje de éxito, campo "Assigned To" limpio, historial actualizado.

Resultados esperados:
  - Paso 4: El botón Delete está ausente o deshabilitado para el usuario con assets.
  - Paso 5 (si aplica): Mensaje de error "Cannot delete user" o similar.
  - Paso 6-7: Checkin exitoso; "Assigned To" queda vacío; historial registra el evento.
  - El sistema maneja el edge case sin errores ni estados inconsistentes.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage
from pages.user_page import UserPage

STATUS_LABEL = "Ready to Deploy"
NOTES_TEXT   = "TC017 - Checkin tras intento de eliminación de usuario asignado"


@pytest.mark.checkout
class TestCheckinUsuarioEliminado:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, logged_in_driver, base_url, request):
        """
        Precondición: garantizar un asset Deployed asignado a un usuario.
        Realiza checkout automático si no hay ninguno disponible.
        Todos los datos quedan en request.cls para ser usados por cada test.
        """
        # --- Garantizar asset en estado Deployed ---
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip(
                    "No hay assets Deployed ni RTD disponibles para checkout; "
                    "precondición TC017 no cumplida."
                )

        # --- Navegar al formulario de checkin para obtener asset_id ---
        checkin = CheckinPage(logged_in_driver, base_url)
        checkin.navigate_to_first_checkin(base_url)
        asset_id = checkin.get_asset_id_from_url()

        if not asset_id:
            pytest.skip("No se pudo obtener el ID del asset; precondición TC017 no cumplida.")

        # --- Navegar al detalle del asset para obtener el usuario asignado ---
        user_page = UserPage(logged_in_driver, base_url)
        checkin.navigate_to_asset_detail(asset_id)

        assigned_user_id   = user_page.get_assigned_user_id_from_asset_detail()
        assigned_user_name = user_page.get_assigned_user_name_from_asset_detail()

        if not assigned_user_id:
            pytest.skip(
                f"El asset {asset_id} no tiene usuario asignado detectable; "
                "precondición TC017 no cumplida."
            )

        # --- Almacenar estado compartido en la clase ---
        request.cls.asset_id           = asset_id
        request.cls.assigned_user_id   = assigned_user_id
        request.cls.assigned_user_name = assigned_user_name
        request.cls.checkin            = checkin
        request.cls.user_page          = user_page
        request.cls.base_url           = base_url
        request.cls.driver             = logged_in_driver

    # ------------------------------------------------------------------
    # Grupo 1: Verificar que el sistema BLOQUEA la eliminación del usuario
    # ------------------------------------------------------------------

    def test_usuario_tiene_asset_asignado(self):
        """El asset debe estar asignado a un usuario antes del intento de eliminación."""
        self.checkin.navigate_to_asset_detail(self.asset_id)
        user_name = self.user_page.get_assigned_user_name_from_asset_detail()

        assert user_name and user_name.strip() not in ("", "—"), (
            f"El asset {self.asset_id} debería estar asignado a un usuario, "
            f"pero el campo 'Assigned To' está vacío o no es detectable."
        )

    def test_eliminacion_usuario_bloqueada(self):
        """El sistema debe BLOQUEAR la eliminación del usuario mientras tiene assets asignados.

        Snipe-IT valida esto en DeleteUserRequest (assigned_assets debe ser 0).
        En la UI, el botón Delete está ausente o deshabilitado cuando isDeletable()
        devuelve false.
        """
        self.user_page.navigate_to_user(self.assigned_user_id)

        delete_bloqueado = self.user_page.is_delete_blocked()

        assert delete_bloqueado, (
            f"El sistema NO bloqueó la eliminación del usuario {self.assigned_user_id} "
            f"({self.assigned_user_name}) que tiene el asset {self.asset_id} asignado. "
            "Se esperaba que el botón Delete estuviera ausente o deshabilitado."
        )

    def test_usuario_sigue_existiendo_tras_intento_fallido(self):
        """El usuario debe permanecer en el sistema tras el intento de eliminación bloqueado."""
        self.user_page.navigate_to_user(self.assigned_user_id)

        assert self.user_page.user_still_exists(self.assigned_user_id), (
            f"El usuario {self.assigned_user_id} ({self.assigned_user_name}) "
            "no existe o no es accesible; el sistema podría haber permitido su borrado."
        )

    # ------------------------------------------------------------------
    # Grupo 2: Realizar el checkin correctamente y verificar resultados
    # ------------------------------------------------------------------

    def test_checkin_exitoso_tras_bloqueo(self):
        """Tras verificar el bloqueo, el checkin del asset debe completarse sin errores."""
        self.checkin.navigate_to_asset_detail(self.asset_id)

        # Navegar directamente al formulario de checkin del asset
        self.driver.get(f"{self.base_url}/hardware/{self.asset_id}/checkin")

        try:
            self.checkin.select_status_by_name(STATUS_LABEL)
        except RuntimeError:
            self.checkin.select_status()

        self.checkin.set_notes(NOTES_TEXT)
        self.checkin.submit()

        assert self.checkin.is_success(), (
            "El checkin del asset falló tras haber verificado el bloqueo de "
            "eliminación del usuario asignado. Se esperaba un checkin exitoso."
        )

    def test_campo_assigned_to_limpio_tras_checkin(self):
        """Después del checkin, el campo 'Assigned To' debe quedar vacío."""
        self.checkin.navigate_to_asset_detail(self.asset_id)

        assert self.user_page.is_assigned_to_empty(), (
            f"El campo 'Assigned To' del asset {self.asset_id} no quedó vacío "
            "después del checkin. El asset podría seguir vinculado al usuario."
        )

    def test_boton_checkout_visible_tras_checkin(self):
        """El botón Checkout debe estar visible (no Checkin) tras devolver el asset."""
        self.checkin.navigate_to_asset_detail(self.asset_id)

        assert self.checkin.is_checkout_button_visible(), (
            f"El botón Checkout no aparece en el detalle del asset {self.asset_id} "
            "tras el checkin. El asset podría seguir en estado Deployed."
        )

    def test_historial_registra_checkin(self):
        """El historial del asset debe registrar el evento de checkin."""
        self.checkin.navigate_to_asset_detail(self.asset_id)
        self.checkin.open_history_tab()

        assert self.checkin.history_has_checkin_record(), (
            f"No se encontró un registro de 'checkin' en el historial del asset "
            f"{self.asset_id}. El evento de devolución no fue registrado."
        )

    def test_historial_contiene_notas_del_checkin(self):
        """Las notas del checkin deben aparecer en el historial del asset."""
        self.checkin.navigate_to_asset_detail(self.asset_id)
        self.checkin.open_history_tab()

        assert self.checkin.history_has_note(NOTES_TEXT), (
            f"Las notas '{NOTES_TEXT}' no aparecen en el historial del asset "
            f"{self.asset_id}. Las notas del checkin no fueron guardadas correctamente."
        )

    # ------------------------------------------------------------------
    # Test integral: verifica todos los criterios de aceptación en un solo paso
    # ------------------------------------------------------------------

    def test_edge_case_completo_sin_errores(self):
        """
        Verifica todos los criterios del caso de uso en una sola ejecución:
        (1) La eliminación del usuario estuvo bloqueada correctamente.
        (2) El checkin se completó sin errores.
        (3) El campo Assigned To quedó limpio.
        (4) El historial registra el evento de checkin.

        Si alguna condición falla, reporta todos los errores encontrados.
        """
        errores = []

        # (1) Bloqueo de eliminación
        self.user_page.navigate_to_user(self.assigned_user_id)
        if not self.user_page.is_delete_blocked():
            errores.append(
                f"El sistema NO bloqueó la eliminación del usuario {self.assigned_user_id} "
                f"con el asset {self.asset_id} asignado."
            )

        # (2) Checkin exitoso
        self.driver.get(f"{self.base_url}/hardware/{self.asset_id}/checkin")
        try:
            self.checkin.select_status_by_name(STATUS_LABEL)
        except RuntimeError:
            self.checkin.select_status()
        self.checkin.set_notes(NOTES_TEXT + " [integral]")
        self.checkin.submit()

        if not self.checkin.is_success():
            errores.append(
                f"El checkin del asset {self.asset_id} no fue exitoso."
            )

        # (3) Assigned To vacío
        self.checkin.navigate_to_asset_detail(self.asset_id)
        if not self.user_page.is_assigned_to_empty():
            errores.append(
                f"El campo 'Assigned To' del asset {self.asset_id} no quedó vacío."
            )

        # (4) Historial actualizado
        self.checkin.open_history_tab()
        if not self.checkin.history_has_checkin_record():
            errores.append(
                f"No se registró el evento de checkin en el historial del asset {self.asset_id}."
            )

        assert not errores, (
            "El edge case 'usuario eliminado + checkin' presenta los siguientes fallos:\n"
            + "\n".join(f"  - {e}" for e in errores)
        )
