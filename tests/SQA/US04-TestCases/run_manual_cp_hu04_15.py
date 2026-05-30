"""
Ejecucion ASISTIDA del caso manual CP-HU04-15
Usabilidad y navegacion por teclado del flujo de checkout.

Este script NO es un test automatizado de pass/fail: es una herramienta de
asistencia para la ejecucion manual. Abre el flujo real, navega con teclado,
registra el orden de foco y captura evidencia para que el tester evalue la
usabilidad. Los resultados se vuelcan en evidence/ y se resumen en consola.

Uso:
    python run_manual_cp_hu04_15.py
"""
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from conftest import (
    BASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD,
    _api, _first_category_id,
)

EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "evidence")
DATE = time.strftime("%Y-%m-%d")


def snap(page, name):
    path = os.path.join(EVIDENCE_DIR, f"{DATE}_CP-HU04-15_{name}.png")
    page.screenshot(path=path)
    print(f"  [evidencia] {path}")
    return path


def describe_active_element(page):
    """Devuelve una descripcion legible del elemento con foco actual."""
    return page.evaluate("""() => {
        const el = document.activeElement;
        if (!el) return 'NINGUNO';
        const tag = el.tagName.toLowerCase();
        const text = (el.innerText || el.value || el.getAttribute('placeholder') || '').trim().slice(0, 40);
        const id = el.id ? '#' + el.id : '';
        const name = el.getAttribute('name') ? '[name=' + el.getAttribute('name') + ']' : '';
        const cls = el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '';
        return `${tag}${id}${name}${cls} :: "${text}"`;
    }""")


def main():
    print("=" * 70)
    print("CP-HU04-15 - Usabilidad y navegacion por teclado del flujo de checkout")
    print("=" * 70)

    # --- Preparar datos via API ---
    print("\n[setup] Creando licencia y usuario de prueba via API...")
    cat_id = _first_category_id()
    lic = _api("POST", "/licenses", {"name": "LIC-HU04-15", "seats": 3, "category_id": cat_id}).get("payload", {})
    lic_id = lic["id"]
    uid = uuid.uuid4().hex[:8]
    user = _api("POST", "/users", {
        "first_name": "Juan", "last_name": "Perez",
        "username": f"juan.perez.{uid}",
        "email": f"juan.perez.{uid}@test.local",
        "password": "TestPass123!", "password_confirmation": "TestPass123!",
        "activated": True,
    }).get("payload", {})
    user_id = user["id"]
    print(f"  Licencia LIC-HU04-15 (id={lic_id}, seats=3)")
    print(f"  Usuario Juan Perez (id={user_id})")

    focus_order = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=400)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()

        # --- Login ---
        print("\n[paso 1] Login como gestor...")
        page.goto(f"{BASE_URL}/login")
        page.fill("input[name='username']", ADMIN_USERNAME)
        page.fill("input[name='password']", ADMIN_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("load")

        # --- Abrir detalle de licencia ---
        print("[paso 2] Abriendo el detalle de la licencia...")
        page.goto(f"{BASE_URL}/licenses/{lic_id}")
        page.wait_for_load_state("networkidle")
        snap(page, "01_detalle_licencia")

        # --- Abrir formulario de checkout ---
        print("[paso 3] Abriendo el formulario de checkout...")
        page.goto(f"{BASE_URL}/licenses/{lic_id}/checkout")
        page.wait_for_load_state("networkidle")
        snap(page, "02_formulario_checkout")

        # --- Navegacion por teclado: registrar orden de foco ---
        print("[paso 4] Navegando con Tab y registrando orden de foco...\n")
        page.locator("body").click()  # foco inicial en el documento
        page.keyboard.press("Tab")
        for i in range(15):
            desc = describe_active_element(page)
            focus_order.append(desc)
            print(f"  Tab {i+1:2d}: {desc}")
            page.keyboard.press("Tab")
            time.sleep(0.15)

        snap(page, "03_navegacion_teclado")

        # --- Verificar etiquetas clave ---
        print("\n[paso 5] Verificando claridad de etiquetas...")
        content = page.content().lower()
        labels = {
            "Checkout / Check Out": "checkout" in content or "check out" in content,
            "Checkout to / assigned_to": "assigned_to" in content or "checkout to" in content.replace("check out", "checkout"),
            "Boton de submit": page.locator("form:has(select[name='assigned_to']) button[type='submit']").count() > 0,
        }
        for label, present in labels.items():
            print(f"  {'[OK]' if present else '[!!]'} {label}: {'presente' if present else 'NO ENCONTRADO'}")

        # --- Completar el checkout con teclado para ver el mensaje de exito ---
        print("\n[paso 6] Completando checkout para evaluar legibilidad del mensaje...")
        page.evaluate(
            """([uid, uname]) => {
                const s = document.getElementById('assigned_user_select');
                if (s) {
                    const o = new Option(uname, uid, true, true);
                    s.add(o);
                    if (window.$ && $(s).data('select2')) $(s).val(uid).trigger('change');
                    else { s.value = uid; s.dispatchEvent(new Event('change', {bubbles:true})); }
                }
            }""",
            [str(user_id), "Juan Perez"],
        )
        page.locator("form:has(select[name='assigned_to']) button[type='submit']").click()
        page.wait_for_load_state("networkidle")

        flash = ""
        alert = page.locator(".alert").first
        if alert.count() > 0:
            flash = alert.inner_text().strip()
        print(f"  Mensaje mostrado: {flash!r}")
        snap(page, "04_mensaje_confirmacion")

        ctx.close()
        browser.close()

    # --- Limpieza ---
    print("\n[teardown] Limpiando datos de prueba...")
    time.sleep(1)
    _api("DELETE", f"/users/{user_id}")
    time.sleep(1)
    _api("DELETE", f"/licenses/{lic_id}")
    print("  Datos eliminados.")

    # --- Resumen ---
    print("\n" + "=" * 70)
    print("RESUMEN - completar las observaciones en cases/CP-HU04-15.md")
    print("=" * 70)
    print(f"Elementos en el orden de foco capturados: {len(focus_order)}")
    print("Evidencia guardada en: evidence/")
    print("\nRevisar manualmente:")
    print("  - El orden de foco es logico (no salta de forma confusa)")
    print("  - Las etiquetas Checkout / Checkout to / Checkout License son claras")
    print("  - El mensaje de confirmacion es legible y no aparece cortado")
    print("  - No hay errores visuales en las capturas")


if __name__ == "__main__":
    main()
