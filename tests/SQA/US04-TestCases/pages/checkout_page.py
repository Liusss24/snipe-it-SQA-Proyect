from playwright.sync_api import Page


class CheckoutPage:
    """
    Wraps /licenses/{id}/checkout.

    Select2 (name="assigned_to", id="assigned_user_select") is controlled via
    page.evaluate() + jQuery because it uses an AJAX data source; direct DOM
    interaction with the hidden <select> is the most reliable approach.
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self, license_id: int):
        self.page.goto(f"{self.base_url}/licenses/{license_id}/checkout")
        self.page.wait_for_load_state("load")

    # ------------------------------------------------------------------
    # Form interaction
    # ------------------------------------------------------------------

    def select_user(self, user_id: int, user_name: str = ""):
        """
        Sets the 'Checkout to' Select2 to the given user.
        Uses jQuery/Select2 programmatic API (AJAX source requires creating the
        Option object before calling .val().trigger('change')).
        """
        self.page.wait_for_selector("#assigned_user_select", state="attached", timeout=5000)
        self.page.evaluate(
            """([userId, userName]) => {
                var select = document.getElementById('assigned_user_select');
                if (!select) return;
                var opt = new Option(userName, userId, true, true);
                select.add(opt);
                if (window.$ && $(select).data('select2')) {
                    $(select).val(userId).trigger('change');
                } else {
                    select.value = userId;
                    select.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }""",
            [str(user_id), user_name],
        )

    def submit(self):
        """Clicks the checkout form's submit button (scoped to the form that has assigned_to)."""
        self.page.locator("form:has(select[name='assigned_to']) button[type='submit']").click()
        self.page.wait_for_load_state("load")

    def double_click_submit(self):
        btn = self.page.locator("form:has(select[name='assigned_to']) button[type='submit']")
        btn.dblclick()
        self.page.wait_for_load_state("load")

    def cancel(self):
        cancel = self.page.locator("a:has-text('Cancel'), button:has-text('Cancel')")
        if cancel.count() > 0:
            cancel.first.click()
        else:
            self.page.go_back()
        self.page.wait_for_load_state("load")

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
        errors = self.page.locator(".invalid-feedback, .help-block.error, .has-error .help-block")
        return [errors.nth(i).inner_text().strip() for i in range(errors.count())]

    def has_no_seats_warning(self) -> bool:
        content = self.page.content().lower()
        return any(p in content for p in [
            "no available seats",
            "there are no seats",
            "no seats available",
            "not enough seats",
        ])

    def is_checkout_form_visible(self) -> bool:
        """True if the checkout form with the user-select is present and visible."""
        sel = self.page.locator("select[name='assigned_to']")
        return sel.count() > 0

    def checkout_to_field_is_empty(self) -> bool:
        """True if no user has been selected yet (placeholder still shown)."""
        # The Select2 span shows placeholder text when empty
        placeholder = self.page.locator(".select2-selection__placeholder")
        selected_val = self.page.locator(".select2-selection__rendered")
        if placeholder.count() > 0 and placeholder.first.is_visible():
            return True
        # Also check if the underlying select has no value
        val = self.page.evaluate(
            "() => { var s = document.getElementById('assigned_user_select'); "
            "return s ? s.value : null; }"
        )
        return not val
