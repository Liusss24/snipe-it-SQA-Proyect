from playwright.sync_api import Page


class AssetCreatePage:
    """
    Wraps the Snipe-IT asset creation form (/hardware/create).

    Real selectors (Snipe-IT v8):
      - Asset Name      -> #name
      - Asset Tag       -> #asset_tag           (name="asset_tags[1]")
      - Serial          -> input[name='serials[1]']  (id literal "serials[1]")
      - Model           -> #model_select_id      (Select2 AJAX, name=model_id)
      - Status Label    -> #status_select_id      (Select2 prepopulado, name=status_id)
      - Default Location-> #rtd_location_id_location_select (Select2 AJAX, name=rtd_location_id)
      - Submit (Save)   -> #submit_button
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    # Snipe-IT v8 organiza el formulario en pestañas personalizadas
    # (componente "snipetab"). Los campos viven en paneles .tab-pane que
    # están ocultos salvo el activo. Para automatizar el formulario completo
    # revelamos todos los paneles tras cargar la página.
    _REVEAL_TABS_JS = """() => {
        document.querySelectorAll('.tab-pane').forEach(p => {
            p.classList.add('active', 'in', 'show');
            p.classList.remove('fade');
            p.style.display = 'block';
            p.style.opacity = '1';
        });
    }"""

    def navigate(self):
        self.page.goto(f"{self.base_url}/hardware/create")
        self.page.wait_for_load_state("networkidle")
        self._reveal_all_tabs()

    def _reveal_all_tabs(self):
        self.page.evaluate(self._REVEAL_TABS_JS)
        self.page.wait_for_timeout(200)

    # ------------------------------------------------------------------
    # Field helpers
    # ------------------------------------------------------------------

    def fill_name(self, name: str):
        self.page.fill("#name", name)

    def fill_asset_tag(self, tag: str):
        self.page.fill("#asset_tag", tag)

    def fill_serial(self, serial: str):
        self.page.fill("input[name='serials[1]']", serial)

    def _set_select2(self, select_id: str, value, label: str = ""):
        """Set a Select2 (AJAX or prepopulated) by option value via JS + change event."""
        self.page.evaluate(
            """([sid, val, lbl]) => {
                const s = document.getElementById(sid);
                if (!s) return;
                // Crear la opción si no existe (necesario para fuentes AJAX)
                if (!Array.from(s.options).some(o => o.value == val)) {
                    s.add(new Option(lbl || val, val, true, true));
                }
                if (window.$ && $(s).data('select2')) {
                    $(s).val(val).trigger('change');
                } else {
                    s.value = val;
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }""",
            [select_id, str(value), label],
        )

    def select_model(self, model_id: int, model_name: str = ""):
        self._set_select2("model_select_id", model_id, model_name)

    def select_status(self, status_id: int, status_name: str = ""):
        self._set_select2("status_select_id", status_id, status_name)

    def select_location(self, location_id: int, location_name: str = ""):
        self._set_select2("rtd_location_id_location_select", location_id, location_name)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def submit(self):
        self.page.locator("#submit_button").click()
        self.page.wait_for_load_state("networkidle")

    def fill_form(self, *, name, serial, model_id, model_name="",
                  status_id=None, status_name="", location_id=None,
                  location_name="", asset_tag=None):
        """Convenience: fills the standard creation fields."""
        if asset_tag is not None:
            self.fill_asset_tag(asset_tag)
        self.fill_name(name)
        self.select_model(model_id, model_name)
        if status_id is not None:
            self.select_status(status_id, status_name)
        self.fill_serial(serial)
        if location_id is not None:
            self.select_location(location_id, location_name)

    # ------------------------------------------------------------------
    # Assertion helpers
    # ------------------------------------------------------------------

    def get_flash_message(self) -> str:
        alert = self.page.locator(".alert").first
        if alert.count() == 0:
            return ""
        try:
            alert.wait_for(state="visible", timeout=3000)
            return alert.inner_text().strip()
        except Exception:
            return ""

    def get_validation_errors(self) -> list[str]:
        errors = self.page.locator(
            ".alert-danger li, .invalid-feedback, .help-block.error, "
            ".has-error .help-block, .text-danger"
        )
        out = []
        for i in range(errors.count()):
            t = errors.nth(i).inner_text().strip()
            if t:
                out.append(t)
        return out

    def page_text(self) -> str:
        return self.page.content().lower()

    def is_on_create_form(self) -> bool:
        """True if still on the creation form (i.e. not redirected after success)."""
        return "/hardware/create" in self.page.url or self.page.locator("#name").count() > 0
