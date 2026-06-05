# DEF-US01-01 — Asset Name de 256 caracteres se acepta y se trunca a 191 sin error

| Campo | Valor |
|-------|-------|
| **ID** | DEF-US01-01 |
| **Caso asociado** | CP-HU01-13 |
| **Módulo** | Assets > Create New — campo Asset Name |
| **Severidad** | Media |
| **Prioridad** | Media |
| **Tipo** | Defecto de validación – ausencia de restricción de longitud en el servidor |
| **Estado** | Abierto |

## Descripción

En Snipe-IT v8.4.0, el campo **Asset Name** (`name`) en el formulario de creación de activos tiene un atributo HTML `maxlength=191` (límite de la columna `varchar(191)` en la base de datos). Sin embargo, el sistema **no valida la longitud en el servidor**.

Al enviar un nombre de 256 caracteres omitiendo el `maxlength` del cliente (comportamiento reproducible con Playwright que bypasea atributos HTML), Snipe-IT:
1. Acepta la solicitud y devuelve "Asset created successfully".
2. Almacena el nombre **truncado a 191 caracteres** en la base de datos.
3. No muestra ningún mensaje de error al usuario.

## Pasos para reproducir

1. Iniciar sesión como administrador en `http://localhost:8000`.
2. Ir a Assets > Create New.
3. Usando automatización (Playwright / script / curl), enviar el campo `name` con 256 caracteres (e.g. `"A" * 256`) ignorando el `maxlength=191` del HTML.
4. Completar los demás campos con datos válidos (Asset Tag único, modelo, serial, status, location).
5. Enviar el formulario.

## Resultado esperado (según plan)

El sistema rechaza el nombre de 256 caracteres y muestra un error de longitud máxima (255 o 191 caracteres).

## Resultado obtenido

El sistema crea el activo exitosamente. El campo Asset Name queda almacenado con **191 caracteres** (truncado) sin ningún mensaje de validación.

## Análisis

Snipe-IT delega la validación de longitud al cliente (atributo `maxlength`). El backend no aplica una regla `max:191` (o `max:255`) sobre el campo `name` al procesar la solicitud. Cualquier cliente que omita el `maxlength` puede crear activos con nombres más largos que el límite de la columna, resultando en datos silenciosamente truncados.

## Impacto

Bajo–Medio. En uso normal la interfaz web impide el ingreso de nombres largos. El impacto real afecta principalmente a integraciones vía API o automatización donde el `maxlength` no se respeta; los datos truncados pueden dificultar la búsqueda y la trazabilidad de activos.

## Recomendación

Agregar una regla de validación `max:191` (o `max:255` según la especificación) en el controlador del backend para el campo `name` de activos. Esto garantiza coherencia entre el cliente y el servidor independientemente del canal de entrada.

## Capturas de pantalla

- `2026-06-04_CP-HU01-13_xfail_nombre_256_aceptado.png` — Lista de activos con banner verde "Created successfully" para el activo con 256 'A', confirmando que el sistema no rechazó la creación.
- `2026-06-04_DEF-US01-01_asset_name_truncado_191.png` — Vista de detalle del activo mostrando el Asset Name truncado a 191 caracteres (cadena de 'A' acortada visualmente en la interfaz).

## Trazabilidad al test automatizado

- Test `xfail(strict=True)`: `automated/test_hu01_11_15_ignacio.py` → `test_cp_hu01_13_asset_name_mayor_255`
- El test queda `xfail` porque la primera aserción (`"created successfully" not in page_text()`) falla: el sistema ACEPTA el activo. Si el defecto se corrige, el test pasará (XPASS) y se sabrá que la validación fue añadida.
