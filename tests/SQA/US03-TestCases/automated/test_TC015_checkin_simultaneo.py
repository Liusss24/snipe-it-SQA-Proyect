"""
TC015 - Checkin simultáneo del mismo asset deployed por dos usuarios Admin
Tipo        : Sistema / Concurrencia
Técnica     : Caso límite / Condición de carrera
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Existe al menos un asset en estado "Deployed" asignado a un usuario
  - Usuario Admin principal (admin) con permisos de Checkin
  - Usuario Admin secundario (user2 / Contrasena3) con permisos de Checkin

Pasos:
  1. Asegurar que existe un asset Deployed (checkout automático si no hay)
  2. Usuario 1 (admin) abre el formulario de checkin del asset X
  3. Usuario 2 (user2) abre el mismo formulario de checkin del asset X
  4. Usuario 1 selecciona status y confirma → checkin exitoso
  5. Usuario 2 intenta seleccionar status y confirmar → debe fallar

Resultados esperados:
  - Usuario 1: checkin exitoso ("Asset checked in successfully")
  - Usuario 2: el sistema rechaza la operación (sin mensaje de éxito)
  - El asset queda en estado no-Deployed; el botón Checkin ya no aparece
  - Solo existe un registro de checkin por esta sesión en el historial del asset

Notas de implementación:
  - driver1 reutiliza el fixture de sesión logged_in_driver (admin).
  - driver2 se crea por test; autentica a user2 con su propia sesión de Chrome.
  - Ambos drivers cargan el formulario ANTES de que cualquiera confirme,
    simulando la condición de carrera descrita en el caso de prueba.
  - Snipe-IT valida el estado del asset en el servidor al procesar el POST;
    el segundo checkin debería ser rechazado independientemente de la UI.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage
from pages.login_page import LoginPage

USER2_USERNAME = "user2"
USER2_PASSWORD = "Contrasena3"
NOTES_U1       = "Checkin simultaneo - Usuario Admin 1"


def _new_driver(headless: bool = False) -> webdriver.Chrome:
    """Instancia un driver de Chrome independiente del fixture de sesión."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    driver.maximize_window()
    return driver


@pytest.mark.concurrencia
class TestCheckinSimultaneo:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url, request):
        """
        Antes de cada test:
          - Garantiza un asset Deployed.
          - driver1 (admin) abre el formulario de checkin.
          - driver2 (user2) abre el mismo formulario sin confirmar.
        Después de cada test limpia driver2.
        """
        self.base_url = base_url
        self.driver1  = logged_in_driver
        headless      = request.config.getoption("--headless")

        # --- Garantizar asset Deployed ---
        self.driver1.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(self.driver1, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(self.driver1, base_url)
            if not checkout.checkout_first_available():
                pytest.skip(
                    "No hay activos Deployed ni RTD disponibles; "
                    "precondición TC015 no cumplida."
                )

        # --- driver1 abre el formulario de checkin y captura el asset_id ---
        self.page1 = CheckinPage(self.driver1, base_url)
        self.page1.navigate_to_first_checkin(base_url)
        self.asset_id = self.page1.get_asset_id_from_url()

        if not self.asset_id:
            pytest.skip("No se pudo obtener el ID del asset; precondición TC015 no cumplida.")

        # --- driver2: sesión independiente como user2 ---
        self.driver2 = _new_driver(headless=headless)
        login2 = LoginPage(self.driver2, base_url)
        login2.load()
        login2.login(USER2_USERNAME, USER2_PASSWORD)

        # driver2 navega al MISMO formulario (ambos lo tienen cargado antes de confirmar)
        self.page2 = CheckinPage(self.driver2, base_url)
        self.driver2.get(f"{base_url}/hardware/{self.asset_id}/checkin")
        # Esperar que el formulario cargue en driver2
        try:
            WebDriverWait(self.driver2, 10).until(
                EC.presence_of_element_located((By.ID, "submit_button"))
            )
        except TimeoutException:
            self.driver2.quit()
            pytest.skip(
                "user2 no pudo acceder al formulario de checkin; "
                "verificar permisos de la cuenta."
            )

        yield

        # --- Limpieza driver2 ---
        try:
            self.driver2.quit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Test 1: El primer checkin (usuario Admin) debe ser exitoso
    # ------------------------------------------------------------------

    def test_usuario1_checkin_exitoso(self):
        """Usuario 1 (admin) confirma el checkin primero → debe ser exitoso."""
        self.page1.select_status()
        self.page1.set_notes(NOTES_U1)
        self.page1.submit()

        assert self.page1.is_success(), (
            "El checkin del Usuario 1 (admin) debería ser exitoso, "
            "pero no se encontró el mensaje de confirmación."
        )

    # ------------------------------------------------------------------
    # Test 2: El segundo checkin (user2) debe ser rechazado
    # ------------------------------------------------------------------

    def test_usuario2_checkin_rechazado_despues_del_primero(self):
        """
        Después de que usuario 1 confirma, usuario 2 intenta confirmar
        el mismo asset → el sistema debe rechazar la segunda operación.
        """
        # Paso 1: usuario 1 confirma
        self.page1.select_status()
        self.page1.set_notes(NOTES_U1)
        self.page1.submit()
        assert self.page1.is_success(), (
            "Precondición: el checkin de usuario 1 debe ser exitoso."
        )

        # Paso 2: usuario 2 intenta confirmar (asset ya no está Deployed)
        try:
            self.page2.select_status()
        except Exception:
            # Si el dropdown falla porque el asset cambió de estado, también
            # es evidencia de que el sistema rechazó la operación.
            pass
        try:
            self.page2.submit()
        except Exception:
            pass

        # El sistema NO debe mostrar mensaje de éxito para usuario 2
        assert not self.page2.is_success(), (
            "El sistema permitió un segundo checkin del mismo asset. "
            "Se esperaba que la operación fuera rechazada porque el asset "
            "ya había sido devuelto por el Usuario 1."
        )

    # ------------------------------------------------------------------
    # Test 3: El asset no debe quedar en estado Deployed tras el primer checkin
    # ------------------------------------------------------------------

    def test_asset_no_queda_deployed_tras_primer_checkin(self):
        """
        Tras el checkin del usuario 1, el asset no debe estar Deployed;
        el botón de checkin no debe aparecer en la vista de detalle.
        """
        # Usuario 1 confirma
        self.page1.select_status()
        self.page1.set_notes(NOTES_U1)
        self.page1.submit()
        assert self.page1.is_success(), (
            "Precondición: el checkin de usuario 1 debe ser exitoso."
        )

        # Verificar que el asset ya no tiene botón de checkin (no está Deployed)
        self.driver1.get(f"{self.base_url}/hardware/{self.asset_id}")
        try:
            WebDriverWait(self.driver1, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
            pytest.fail(
                "El asset aún muestra el botón Checkin después de haber sido "
                "devuelto por el Usuario 1. El estado del asset no cambió correctamente."
            )
        except TimeoutException:
            pass  # Correcto: el botón Checkin ya no está visible

    # ------------------------------------------------------------------
    # Test 4: Solo debe registrarse un checkin por este escenario en el historial
    # ------------------------------------------------------------------

    def test_solo_un_registro_checkin_en_historial(self):
        """
        Tras ambos intentos, el historial del asset debe contener exactamente
        un registro del checkin realizado por el usuario 1 (identificado por
        las notas únicas), no uno adicional del intento de usuario 2.
        """
        # Usuario 1 confirma
        self.page1.select_status()
        self.page1.set_notes(NOTES_U1)
        self.page1.submit()
        assert self.page1.is_success(), (
            "Precondición: el checkin de usuario 1 debe ser exitoso."
        )

        # Usuario 2 intenta (puede fallar; esperado)
        try:
            self.page2.select_status()
            self.page2.submit()
        except Exception:
            pass

        # Navegar al historial del asset y contar registros con las notas únicas
        self.driver1.get(f"{self.base_url}/hardware/{self.asset_id}")
        self.page1.open_history_tab()

        # Esperar a que las notas aparezcan en el page_source: Bootstrap-Table
        # renderiza las filas (DOM) antes de que el AJAX pueble las celdas, por lo
        # que presence_of_element_located puede dispararse con celdas aún vacías.
        # Esperar el texto en page_source garantiza que el AJAX terminó de renderizar.
        try:
            WebDriverWait(self.driver1, 20).until(
                lambda d: NOTES_U1.lower() in d.page_source.lower()
            )
        except TimeoutException:
            pytest.fail(
                f"Las notas '{NOTES_U1}' no aparecieron en el historial del asset "
                "en el tiempo esperado. El checkin puede no haberse registrado."
            )

        # Contar filas que contienen las notas únicas del usuario 1
        rows = self.driver1.find_elements(
            By.CSS_SELECTOR, "#history table tbody tr"
        )
        coincidencias = sum(
            1 for row in rows
            if NOTES_U1.lower() in (row.get_attribute("textContent") or "").lower()
        )

        assert coincidencias == 1, (
            f"Se esperaba exactamente 1 registro con las notas '{NOTES_U1}' "
            f"en el historial, pero se encontraron {coincidencias}. "
            "Posible doble registro de checkin por la condición de carrera."
        )
