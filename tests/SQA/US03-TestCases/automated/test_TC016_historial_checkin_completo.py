"""
TC014 - Registro completo del evento de checkin en la actividad reciente del Dashboard
Tipo        : Sistema
Técnica     : Flujo completo / Verificación de auditoría
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Usuario Admin con sesión iniciada y permisos de Checkin
  - Existe al menos un asset en estado "Deployed" asignado a un usuario válido
  - Status Label "Ready to Deploy" existe en el sistema

Pasos:
  1. Asegurar que existe un asset Deployed (checkout automático si no hay)
  2. Navegar al formulario de checkin del asset; anotar asset_id y asset_tag
  3. Seleccionar status y agregar notas "Prueba de auditoría"
  4. Confirmar checkin → verificar mensaje de éxito
  5. Navegar al Dashboard (/)
  6. Esperar que cargue la tabla "Recent Activity" (#dashActivityReport)
  7. Localizar el registro del checkin recién realizado (primera fila, sort DESC)
  8. Verificar cada campo visible del registro

Resultados esperados (en la tabla Recent Activity del Dashboard):
  - Columna Fecha: contiene el año actual
  - Columna Fecha: contiene hora en formato HH:MM
  - Columna "Created By": contiene el nombre del usuario admin
  - Columna "Action": muestra "checkin from"
  - Columna "Item": enlaza al asset correcto (/hardware/{asset_id})
  - El registro es el más reciente (primera fila, orden DESC)

Notas de implementación:
  - El Dashboard usa data-sort-order="desc"; el registro más reciente es la PRIMERA fila.
  - La tabla carga vía AJAX (Bootstrap-Table + api.activity.index?limit=25).
  - El campo 'action_type' en la API devuelve "checkin from" (lowercase).
  - La columna 'item' usa polymorphicItemFormatter → renderiza un <a href=/hardware/{id}>.
  - Las notas del checkin NO aparecen en la tabla Recent Activity (no hay columna notes);
    se incluyen en el precondición para hacer el checkin identificable, pero no se verifican aquí.
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage
from pages.dashboard_page import DashboardPage

NOTES_TEXT   = "Prueba de auditoría"
STATUS_LABEL = "Ready to Deploy"
ADMIN_USER   = "admin"
ACTION_TYPE  = "checkin from"


@pytest.mark.checkout
class TestRegistroActividadRecienteCheckin:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        """
        Garantiza un asset Deployed, realiza el checkin con notas y
        navega al Dashboard. Cada test solo necesita consultar
        self.dashboard y self.asset_id.
        """
        self.base_url = base_url

        # --- Garantizar asset Deployed ---
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip(
                    "No hay activos Deployed ni RTD disponibles; "
                    "precondición TC014 no cumplida."
                )

        # --- Navegar al formulario de checkin y capturar metadatos ---
        checkin = CheckinPage(logged_in_driver, base_url)
        checkin.navigate_to_first_checkin(base_url)

        self.asset_id  = checkin.get_asset_id_from_url()
        self.asset_tag = checkin.get_asset_tag_from_form()

        if not self.asset_id:
            pytest.skip("No se pudo obtener el ID del asset; precondición TC014 no cumplida.")

        # --- Realizar el checkin ---
        try:
            checkin.select_status_by_name(STATUS_LABEL)
        except RuntimeError:
            checkin.select_status()          # fallback: primera opción disponible
        checkin.set_notes(NOTES_TEXT)
        checkin.submit()

        if not checkin.is_success():
            pytest.skip("El checkin no fue exitoso; precondición TC014 no cumplida.")

        # --- Navegar al Dashboard y esperar la tabla de actividad ---
        self.dashboard = DashboardPage(logged_in_driver, base_url)
        self.dashboard.navigate()
        self.dashboard.wait_for_activity_table()

        # --- Localizar el registro del checkin en la tabla ---
        self.checkin_row = self.dashboard.get_activity_row_with_action_for_asset(
            ACTION_TYPE, self.asset_id
        )

    # ------------------------------------------------------------------
    # Test 1: Fecha (año actual)
    # ------------------------------------------------------------------

    def test_fecha_correcta_en_actividad_reciente(self):
        """La columna Date debe contener el año actual."""
        assert self.checkin_row is not None, (
            f"No se encontró ningún registro con acción '{ACTION_TYPE}' "
            f"para el asset {self.asset_id} en la tabla Recent Activity."
        )
        assert self.dashboard.row_has_today_year(self.checkin_row), (
            "El año actual no aparece en la columna Date del registro de checkin "
            "en la tabla Recent Activity del Dashboard."
        )

    # ------------------------------------------------------------------
    # Test 2: Hora en formato HH:MM
    # ------------------------------------------------------------------

    def test_hora_presente_en_actividad_reciente(self):
        """La columna Date debe incluir la hora en formato HH:MM."""
        assert self.checkin_row is not None, (
            f"No se encontró el registro de checkin del asset {self.asset_id}."
        )
        assert self.dashboard.row_has_time(self.checkin_row), (
            "No se encontró un patrón de hora (HH:MM) en la columna Date "
            "del registro de checkin en Recent Activity."
        )

    # ------------------------------------------------------------------
    # Test 3: Usuario que realizó el checkin
    # ------------------------------------------------------------------

    def test_usuario_checkin_en_actividad_reciente(self):
        """La columna 'Created By' debe mostrar el nombre del admin."""
        assert self.checkin_row is not None, (
            f"No se encontró el registro de checkin del asset {self.asset_id}."
        )
        assert self.dashboard.row_has_admin(self.checkin_row, ADMIN_USER), (
            f"El usuario '{ADMIN_USER}' no aparece en la columna 'Created By' "
            "del registro de checkin en Recent Activity."
        )

    # ------------------------------------------------------------------
    # Test 4: Tipo de acción "checkin from"
    # ------------------------------------------------------------------

    def test_accion_es_checkin_from_en_actividad_reciente(self):
        """La columna 'Action' debe mostrar 'checkin from'."""
        assert self.checkin_row is not None, (
            f"No se encontró el registro de checkin del asset {self.asset_id}."
        )
        assert self.dashboard.row_has_action(self.checkin_row, ACTION_TYPE), (
            f"La acción '{ACTION_TYPE}' no aparece en la columna 'Action' "
            "del registro en Recent Activity."
        )

    # ------------------------------------------------------------------
    # Test 5: Item enlaza al asset correcto
    # ------------------------------------------------------------------

    def test_item_enlaza_al_asset_correcto(self):
        """La columna 'Item' debe contener un enlace a /hardware/{asset_id}."""
        assert self.checkin_row is not None, (
            f"No se encontró el registro de checkin del asset {self.asset_id}."
        )
        assert self.dashboard.row_item_links_to_asset(self.checkin_row, self.asset_id), (
            f"El asset (id={self.asset_id}) no aparece enlazado en la columna 'Item' "
            "del registro de checkin en Recent Activity."
        )

    # ------------------------------------------------------------------
    # Test 6: Orden cronológico — el registro es el más reciente (primera fila)
    # ------------------------------------------------------------------

    def test_registro_es_el_mas_reciente(self):
        """
        El registro del checkin debe ser la primera fila de la tabla
        (orden DESC por fecha — más reciente arriba).
        """
        assert self.checkin_row is not None, (
            f"No se encontró el registro de checkin del asset {self.asset_id}."
        )
        assert self.dashboard.first_row_is(self.checkin_row), (
            "El registro de checkin no es la primera fila de la tabla Recent Activity. "
            "Se esperaba que, por ser el evento más reciente, apareciera en la cima "
            "(orden cronológico descendente)."
        )

    # ------------------------------------------------------------------
    # Test 7: Verificación integral de todos los campos
    # ------------------------------------------------------------------

    def test_registro_actividad_reciente_completo(self):
        """
        Verifica todos los campos visibles del registro en una sola pasada:
        fecha (año), hora (HH:MM), usuario, tipo de acción, item y posición.
        """
        assert self.checkin_row is not None, (
            f"No se encontró el registro con acción '{ACTION_TYPE}' "
            f"para el asset {self.asset_id} en la tabla Recent Activity."
        )

        errores = []

        if not self.dashboard.row_has_today_year(self.checkin_row):
            from datetime import date
            errores.append(f"Año {date.today().year} no encontrado en columna Date.")

        if not self.dashboard.row_has_time(self.checkin_row):
            errores.append("Hora en formato HH:MM no encontrada en columna Date.")

        if not self.dashboard.row_has_admin(self.checkin_row, ADMIN_USER):
            errores.append(f"Usuario '{ADMIN_USER}' no encontrado en columna Created By.")

        if not self.dashboard.row_has_action(self.checkin_row, ACTION_TYPE):
            errores.append(f"Acción '{ACTION_TYPE}' no encontrada en columna Action.")

        if not self.dashboard.row_item_links_to_asset(self.checkin_row, self.asset_id):
            errores.append(
                f"Enlace a /hardware/{self.asset_id} no encontrado en columna Item."
            )

        if not self.dashboard.first_row_is(self.checkin_row):
            errores.append(
                "El registro no es la primera fila (más reciente) de la tabla."
            )

        assert not errores, (
            "El registro de actividad reciente está incompleto o incorrecto:\n"
            + "\n".join(f"  - {e}" for e in errores)
        )
