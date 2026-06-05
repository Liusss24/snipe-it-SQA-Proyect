# DEF-US05-01 — Garantía que vence el día actual no aparece en alertas (comparación datetime vs medianoche)

| Campo | Valor |
|-------|-------|
| **ID** | DEF-US05-01 |
| **Caso asociado** | CP-HU05-05 |
| **Módulo** | Assets – Expiration Alerts (comando `snipeit:expiring-alerts`) |
| **Severidad** | Media |
| **Prioridad** | Media |
| **Tipo** | Defecto de lógica – comparación de fechas incorrecta (datetime vs date) |
| **Estado** | Abierto |

## Descripción

En Snipe-IT v8.4.0, el método `getExpiringWarrantyOrEol()` usa `Carbon::now()` (datetime con hora y minutos actuales) como límite inferior del rango `betweenIncluded()`. La fecha de vencimiento de garantía se almacena como `DATE` en MySQL (medianoche, `00:00:00`).

Cuando el test se ejecuta durante el día, `Carbon::now()` apunta a, por ejemplo, `2026-06-04 14:30:00`. Una garantía que vence hoy tiene fecha `2026-06-04 00:00:00`. Como `00:00:00 < 14:30:00`, el valor queda **fuera** del rango `betweenIncluded(now, now+30d)` y no se incluye en las alertas.

## Pasos para reproducir

1. Crear un activo con `purchase_date = hoy − 365 días` y `warranty_months = 12` (garantía calculada = hoy `00:00:00`).
2. Ejecutar `php artisan snipeit:expiring-alerts` en cualquier momento después de la medianoche.
3. Observar que el activo **no** aparece en el output.

## Resultado esperado (según plan)

Un activo cuya garantía vence el día actual debe ser incluido en las alertas como elemento vigente (límite inferior inclusivo).

## Resultado obtenido

El activo no aparece en el output de `snipeit:expiring-alerts`. La comparación `betweenIncluded(Carbon::now(), Carbon::now()->addDays(30))` excluye las fechas `DATE` almacenadas como medianoche cuando la ejecución ocurre pasada la medianoche.

## Análisis

El bug está en el uso de `Carbon::now()` en lugar de `Carbon::today()` (o `Carbon::now()->startOfDay()`) para el límite inferior. La corrección consistiría en cambiar el límite inferior a `Carbon::today()` para que cualquier garantía cuya fecha de vencimiento sea el día actual (sin importar la hora) quede incluida en el rango.

## Impacto

Bajo–Medio. Los activos cuya garantía vence exactamente hoy no generan alerta, lo cual puede causar que el administrador no tome acción preventiva en el último día de cobertura de garantía.

## Recomendación

Cambiar en `getExpiringWarrantyOrEol()` el límite inferior de `Carbon::now()` a `Carbon::today()` (medianoche del día actual) para que los activos con vencimiento el día de hoy sean correctamente incluidos en el umbral.

## Capturas de pantalla

- `2026-06-04_US05_activos_garantia_eol.png` — Lista de activos con garantías/EOL configurados; ACT-HU05-02 no aparece en el output de alertas pese a tener garantía vencida el día actual.
- `2026-06-04_US05_output_expiring_alerts.txt` — Output de `snipeit:expiring-alerts` que no incluye el activo con garantía que vence hoy (ausencia confirma el defecto).

## Trazabilidad al test automatizado

- Test `xfail(strict=True)`: `automated/test_hu05_04_07_garantias_activos.py` → `test_cp_hu05_05_garantia_vence_hoy`
- Si el defecto se corrige, el test pasará (XPASS) indicando que la lógica de comparación fue arreglada.
