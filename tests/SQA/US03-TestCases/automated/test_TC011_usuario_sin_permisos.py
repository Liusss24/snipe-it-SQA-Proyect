"""
TC011 - Usuario sin permisos intenta Checkin
Tipo        : Sistema
Técnica     : Control de permisos / Prueba negativa
Ejecución   : Automatizada
Prioridad   : Alta (Seguridad)
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Usuario "user1" sin permiso "Checkin Assets"
  - Asset en estado Deployed visible en el listado

Pasos:
  1. Login como user1 / ContrasenaUser
  2. Navegar a Assets → List All (/hardware)
  3. Observar las opciones disponibles en la columna de acciones

Resultados esperados:
  - Botón "Checkin" no visible en el listado
  - El sistema no permite iniciar el flujo de devolución
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from pages.login_page import LoginPage

USER1_USERNAME = "user1"
USER1_PASSWORD = "ContrasenaUser"


@pytest.mark.assets
class TestUsuarioSinPermisos:

    @pytest.fixture(scope="class")
    def user1_driver(self, base_url):
        """Driver independiente con sesión de user1.

        Se crea aparte del logged_in_driver (admin) para no contaminar
        la sesión de administrador usada por los demás test cases.
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        drv = webdriver.Chrome(service=service, options=options)
        drv.implicitly_wait(10)
        drv.maximize_window()

        login = LoginPage(drv, base_url)
        login.load()
        login.login(USER1_USERNAME, USER1_PASSWORD)

        yield drv
        drv.quit()

    @pytest.fixture(autouse=True)
    def setup(self, user1_driver, base_url):
        self.driver   = user1_driver
        self.base_url = base_url

    def test_checkin_no_visible_en_lista(self):
        """user1 sin permisos no debe ver el botón Checkin en la lista de assets."""
        self.driver.get(f"{self.base_url}/hardware")

        # Esperar a que la página termine de cargar (tabla AJAX)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "table.snipe-table, .alert, #main-content")
                )
            )
        except TimeoutException:
            pass

        checkin_buttons = self.driver.find_elements(
            By.CSS_SELECTOR, "a.btn-checkin"
        )
        assert len(checkin_buttons) == 0, \
            (f"user1 ve {len(checkin_buttons)} botón(es) Checkin en el listado "
             f"sin tener el permiso 'Checkin Assets'.")

    def test_acceso_directo_denegado(self):
        """Acceder directamente a /hardware/{{id}}/checkin debe ser denegado."""
        self.driver.get(f"{self.base_url}/hardware/1/checkin")

        page = self.driver.page_source.lower()

        denegado = (
            "403" in self.driver.current_url
            or "403" in page
            or "permission" in page
            or "unauthorized" in page
            or "forbidden" in page
            or "denied" in page
            or "/login" in self.driver.current_url
        )

        assert denegado, \
            ("user1 pudo acceder a la URL de checkin directamente; "
             "el sistema debería denegar el acceso.")
