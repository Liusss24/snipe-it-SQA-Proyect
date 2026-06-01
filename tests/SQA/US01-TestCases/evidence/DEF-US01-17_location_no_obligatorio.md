# DEF-US01-17 — Location no es campo obligatorio en creación de activos

| Campo | Valor |
|-------|-------|
| **ID** | DEF-US01-17 |
| **Caso asociado** | CP-HU01-17 |
| **Módulo** | Assets > Create New — campo Default Location |
| **Severidad** | Media |
| **Prioridad** | Media |
| **Tipo** | Defecto de validación (comportamiento vs. especificación) |
| **Estado** | Abierto |

## Descripción

En Snipe-IT v8.4.0, el campo **Default Location** (`rtd_location_id`) en el formulario de creación de activos no es obligatorio. El sistema permite guardar un activo sin seleccionar ninguna ubicación, dejando el campo como `null` en la base de datos.

El Plan de Pruebas (CP-HU01-17) especifica que el sistema debe rechazar la creación de un activo sin ubicación, mostrando un mensaje de validación. Este comportamiento no se cumple.

## Pasos para reproducir

1. Iniciar sesión como administrador en `http://localhost:8000`.
2. Ir a Assets > Create New.
3. Completar el formulario con: Asset Tag, Asset Name "Laptop sin ubicacion QA", Model Dell Latitude 5420, Serial SN-AST-1017, Status Label Ready to Deploy.
4. **Omitir** el campo Default Location / Location.
5. Presionar Save.

## Resultado esperado (según plan)

El sistema muestra un error de validación en el campo Location y no guarda el activo.

## Resultado obtenido

El sistema crea el activo exitosamente y muestra "Asset created successfully". El activo queda registrado con `rtd_location_id = null`. No se muestra ningún mensaje de validación relacionado con la ubicación.

## Análisis

Snipe-IT no impone restricción `NOT NULL` ni regla de validación de negocio sobre `rtd_location_id` para activos. Este comportamiento es intencional en el diseño del sistema: un activo puede existir sin ubicación asignada (por ejemplo, en tránsito o almacén sin clasificar). El Plan de Pruebas asumió que la ubicación es obligatoria, lo cual no refleja el comportamiento real de la aplicación.

## Impacto

Bajo–Medio. Los activos sin ubicación siguen siendo válidos en Snipe-IT, pero dificultan la trazabilidad de inventario y los reportes de ubicación. En entornos con políticas estrictas de localización, esto puede generar datos incompletos.

## Recomendación

Si la organización requiere que todo activo tenga ubicación al momento de creación, evaluar la posibilidad de agregar validación personalizada a nivel de configuración o flujo de negocio. Alternativamente, actualizar el Plan de Pruebas para reflejar el comportamiento real del sistema.

## Trazabilidad al test automatizado

- Test `xfail`: `automated/test_hu01_17_18_location_negative.py` → `test_cp_hu01_17_bloqueo_sin_location`
- Test complementario (comportamiento real): `test_cp_hu01_17b_sistema_permite_crear_sin_location` → Pass ✅
