"""
CP-HU01-16 – Bloqueo de acceso al formulario de creación para usuario sin permisos
"""
import pytest
from conftest import asset_exists_by_serial, BASE_URL


@pytest.mark.sistema
@pytest.mark.negative
@pytest.mark.high
def test_cp_hu01_16_bloqueo_acceso_sin_permisos(noperm_page, base_url):
    """
    Verifica que un usuario sin permisos para crear activos no puede acceder al
    formulario Assets > Create New, ni por menú ni navegando directamente a la URL.
    Técnica: Control de permisos.

    Precondición: existe el usuario 'viewer' sin privilegios de creación en Assets.
    """
    page = noperm_page

    # --- Paso 1: verificar que el menú no ofrece la opción Create ---
    # Snipe-IT renderiza el botón "Create New" en la barra de Assets solo si el
    # usuario tiene el permiso create. Buscamos el enlace /hardware/create en el nav.
    page.goto(f"{base_url}/hardware")
    page.wait_for_load_state("networkidle")

    create_link = page.locator("a[href*='/hardware/create']")
    assert create_link.count() == 0, (
        "El enlace 'Create New' no debería aparecer en el menú para un usuario sin permisos"
    )

    # --- Paso 2: intentar acceder directamente por URL ---
    page.goto(f"{base_url}/hardware/create")
    page.wait_for_load_state("networkidle")

    current_url = page.url
    page_content = page.content().lower()

    # El sistema debe denegar el acceso: redirigir fuera del formulario o mostrar 403.
    # Criterios de éxito (cualquiera de los tres):
    #   a) La URL ya no es /hardware/create (hubo redirect)
    #   b) El contenido muestra "403" o "forbidden" o "unauthorized"
    #   c) El formulario de creación (#submit_button o #asset_tag) no está presente
    redirected_away = "/hardware/create" not in current_url
    shows_denial    = any(s in page_content for s in ("403", "forbidden", "unauthorized",
                                                       "not authorized", "permission denied",
                                                       "you are not authorized"))
    form_absent     = page.locator("#asset_tag").count() == 0

    assert redirected_away or shows_denial or form_absent, (
        f"El usuario sin permisos pudo acceder al formulario de creación. "
        f"URL actual: {current_url!r}"
    )

    # --- Verificación de integridad: no se creó ningún activo residual ---
    assert not asset_exists_by_serial("SN-AST-1016"), (
        "Se encontró un activo con serial SN-AST-1016; posible creación indebida"
    )
