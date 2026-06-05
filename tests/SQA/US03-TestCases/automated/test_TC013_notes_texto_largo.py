"""
TC013 - Notes con longitud máxima (1000+ caracteres)
Tipo        : Sistema
Técnica     : Valores límite
Ejecución   : Automatizada
Prioridad   : Media
Encargado   : Mariana Acuña Rodríguez

Precondiciones:
  - Asset en estado Deployed asignado a un usuario

Pasos:
  1. Login en Snipe-IT
  2. Click en botón Checkin del asset Deployed
  3. Seleccionar status
  4. Notes: pegar texto de 1000+ caracteres
  5. Click en "Checkin Asset"
  6. Verificar comportamiento del sistema

Resultados esperados:
  - El sistema acepta el texto largo y completa el checkin (resultado primario)
  - O muestra un mensaje de validación claro (resultado alternativo aceptable)
  - En ningún caso se produce un error 500 ni pérdida de datos silenciosa
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage

# Texto del krecorder (~1100 caracteres) más padding para asegurar 1000+
NOTES_TEXT = (
    "En una mañana cualquiera, cuando la ciudad apenas comenzaba a despertar, "
    "las calles estaban cubiertas por una luz suave que transformaba los edificios "
    "comunes en escenarios llenos de posibilidades. Los vendedores abrían sus "
    "negocios, los autobuses iniciaban sus recorridos y las personas salían de sus "
    "hogares con planes, preocupaciones y expectativas distintas. A simple vista "
    "parecía un día ordinario, pero la realidad es que cada jornada contiene miles "
    "de historias que rara vez llegan a conocerse entre sí. "
    "La vida cotidiana está formada por una enorme cantidad de decisiones pequeñas. "
    "Elegimos qué ropa usar, qué camino tomar para llegar a un destino, qué palabras "
    "decir durante una conversación y cómo reaccionar ante los acontecimientos "
    "inesperados. Aunque muchas de estas decisiones parecen insignificantes, con el "
    "tiempo terminan moldeando el rumbo de nuestras experiencias. Un encuentro casual "
    "puede convertirse en una amistad duradera, una idea anotada en una libreta puede "
    "transformarse en un proyecto importante y una simple conversación puede cambiar "
    "la forma en que una persona entiende el mundo."
)

STATUS_LABEL = "Ready to Deploy"


@pytest.mark.checkout
class TestNotesTextoLargo:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, logged_in_driver, base_url, request):
        """Hace el checkin con texto largo UNA vez para toda la clase."""
        logged_in_driver.get(f"{base_url}/hardware?status_type=Deployed")
        try:
            WebDriverWait(logged_in_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-checkin"))
            )
        except TimeoutException:
            checkout = CheckoutPage(logged_in_driver, base_url)
            if not checkout.checkout_first_available():
                pytest.skip("No hay activos Deployed ni RTD; "
                            "precondición TC013 no cumplida.")

        assert len(NOTES_TEXT) >= 1000, \
            f"El texto de prueba tiene solo {len(NOTES_TEXT)} caracteres; debe ser 1000+."

        page = CheckinPage(logged_in_driver, base_url)
        page.navigate_to_first_checkin(base_url)

        request.cls.asset_id = page.get_asset_id_from_url()
        page.select_status_by_name(STATUS_LABEL)
        page.set_notes(NOTES_TEXT)
        page.submit()

        request.cls.page         = page
        request.cls.base_url     = base_url
        request.cls.page_source  = logged_in_driver.page_source.lower()
        request.cls.current_url  = logged_in_driver.current_url

    def test_sin_error_500(self):
        """El sistema no debe producir un error 500 con texto largo en Notes."""
        assert "500" not in self.page_source, \
            "El servidor devolvió error 500 al procesar Notes con texto largo."
        assert "server error" not in self.page_source, \
            "El servidor devolvió un error interno al procesar Notes con texto largo."

    def test_checkin_exitoso_o_validacion(self):
        """El sistema debe aceptar el texto largo o mostrar un error de validación claro."""
        exito     = "checked in" in self.page_source
        error_val = "alert-danger" in self.page_source or "error" in self.page_source

        assert exito or error_val, \
            ("El sistema no mostró ni mensaje de éxito ni error de validación "
             "tras ingresar 1000+ caracteres en Notes.")
