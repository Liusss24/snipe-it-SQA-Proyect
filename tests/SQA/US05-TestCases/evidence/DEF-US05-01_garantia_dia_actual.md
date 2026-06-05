# DEF-US05-01 – Garantías que vencen el día actual son excluidas de las alertas

## Defect ID
DEF-US05-01

## Related test case
CP-HU05-05

## Severity
Low

## Priority
Low

## Snipe-IT version
v8.4.0 (build 21690)

## Description

El método `getExpiringWarrantyOrEol()` del modelo `Asset` usa `Carbon::now()`
(datetime con hora) en la comparación `betweenIncluded($now, $end)`.

Una garantía cuya fecha calculada (`purchase_date + warranty_months`) es la
fecha actual a medianoche (`2026-06-04 00:00:00`) queda **fuera** del rango
cuando el comando se ejecuta en cualquier momento posterior (por ejemplo a las
14:30, `Carbon::now() = 2026-06-04 14:30:00`).

En consecuencia, garantías que vencen "hoy" **no generan alerta** en el día
de vencimiento, lo que viola el criterio definido en CP-HU05-05.

## Root cause

```php
// app/Models/Asset.php – getExpiringWarrantyOrEol()
$now = now();   // ← datetime con hora, no solo fecha
$end = now()->addDays($days);

// La comparación falla para vencimientos a medianoche de hoy:
return $expiration_window->betweenIncluded($now, $end);
// 2026-06-04 00:00:00 >= 2026-06-04 14:30:00  → FALSE
```

## Expected behavior

Garantías que vencen el día actual deberían incluirse en las alertas. La
comparación debería usar `Carbon::today()` (fecha sin hora) o `>=
Carbon::today()->startOfDay()` para capturar el día completo.

## Suggested fix

```php
$now = Carbon::today();   // ← solo fecha (00:00:00)
$end = Carbon::today()->addDays($days)->endOfDay();
```

## Steps to reproduce

1. Crear un activo con `purchase_date = hoy - 365 días` y `warranty_months = 12`.
2. Ejecutar `php artisan snipeit:expiring-alerts` cualquier momento después de medianoche.
3. El activo **no aparece** en el output aunque su garantía vence hoy.

## Test status
- Test CP-HU05-05 marcado como `xfail(strict)` — documenta este defecto.
