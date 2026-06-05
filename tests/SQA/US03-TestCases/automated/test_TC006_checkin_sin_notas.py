"""
TC006 - Devolución exitosa de activo sin notas (campo opcional)
Tipo        : Sistema
Técnica     : Partición de equivalencia (campo opcional vacío)
Ejecución   : Automatizada
Prioridad   : Alta
Encargado   : Mariana Acuña Rodríguez

Precondición: Debe existir al menos un asset en estado "Deployed"
              asignado a un usuario en Snipe-IT antes de correr este test.
"""
import pytest
from pages.checkin_page import CheckinPage
from pages.checkout_page import CheckoutPage


@pytest.mark.checkout
class TestCheckinSinNotas:

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_driver, base_url):
        checkout = CheckoutPage(logged_in_driver, base_url)
        if not checkout.checkout_first_available():
            pytest.skip("No hay activos disponibles para checkout; precondición TC006 no cumplida.")
        self.page     = CheckinPage(logged_in_driver, base_url)
        self.base_url = base_url

    def _do_checkin(self):
        self.page.navigate_to_first_checkin(self.base_url)
        self.page.select_status()
        self.page.clear_notes()
        self.page.submit()

    def test_checkin_exitoso_sin_notas(self):
        """El sistema debe permitir checkin sin ingresar notas."""
        self._do_checkin()

        assert self.page.is_success(), \
            "El checkin falló o no mostró mensaje de éxito con Notes vacío."

    def test_mensaje_confirmacion_correcto(self):
        """Debe mostrarse el mensaje 'Asset checked in successfully'."""
        self._do_checkin()

        mensaje = self.page.get_success_message()
        assert "checked in" in mensaje.lower(), \
            f"El mensaje de éxito no es el esperado. Se obtuvo: '{mensaje}'"

    def test_historial_registra_checkin(self):
        """El historial del asset debe tener un registro de 'Checked In'."""
        self._do_checkin()

        assert self.page.is_success(), "El checkin no fue exitoso."

        self.page.open_history_tab()
        assert self.page.history_has_checkin_record(), \
            "No se encontró el registro de checkin en el historial del asset."
