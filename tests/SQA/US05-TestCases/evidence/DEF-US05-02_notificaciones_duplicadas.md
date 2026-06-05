# DEF-US05-02 — Notificaciones de alerta duplicadas en ejecuciones repetidas del scheduler

| Campo | Valor |
|-------|-------|
| **ID** | DEF-US05-02 |
| **Caso asociado** | CP-HU05-15 |
| **Módulo** | Licenses / Assets – Expiration Alerts (comando `snipeit:expiring-alerts`) |
| **Severidad** | Alta |
| **Prioridad** | Alta |
| **Tipo** | Defecto de lógica – ausencia de deduplicación entre ejecuciones |
| **Estado** | Abierto |

## Descripción

En Snipe-IT v8.4.0, el comando `snipeit:expiring-alerts` no implementa un mecanismo de deduplicación por ejecución. Cada vez que el comando se ejecuta en el mismo día, genera **nuevas entradas en el log** y potencialmente envía **nuevos correos de notificación** por los mismos elementos, aunque ya hayan sido reportados en una ejecución anterior del mismo día.

Comportamiento observado:
- 1.ª ejecución: 2 entradas en log por elemento.
- 2.ª ejecución (mismo día): 2 entradas adicionales → total 4 entradas por el mismo elemento.

## Pasos para reproducir

1. Configurar alertas habilitadas, email activo, umbral 30 días.
2. Crear una licencia con Expiration Date = hoy + 10 días.
3. Ejecutar `php artisan snipeit:expiring-alerts` (1.ª vez) — anotar líneas en `storage/logs/laravel.log`.
4. Ejecutar `php artisan snipeit:expiring-alerts` (2.ª vez, mismo día).
5. Comparar el número de entradas en el log.

## Resultado esperado (según plan)

Cada ejecución diaria genera exactamente una notificación por elemento próximo a vencer. Ejecuciones repetidas no duplican el envío.

## Resultado obtenido

La 1.ª ejecución genera 2 entradas en el log por elemento. La 2.ª ejecución añade 2 entradas más al log, elevando el total a 4. Si el scheduler corre más de una vez al día (o es ejecutado manualmente), el administrador recibe múltiples correos duplicados sobre el mismo vencimiento.

## Análisis

El comando no guarda un registro de qué elementos ya fueron notificados en la fecha actual (no hay tabla de `notifications_sent` ni flag de "ya alertado hoy"). Cada invocación del comando procesa todos los elementos dentro del umbral sin verificar si ya fueron notificados.

La causa raíz probable es la ausencia de lógica `if not already_notified_today(item)` antes del envío de cada notificación.

## Impacto

Alto en ambientes donde el scheduler pueda correr múltiples veces al día o donde el administrador ejecute el comando manualmente. Los usuarios finales reciben correos repetidos sobre el mismo vencimiento, lo que genera ruido y puede llevar a ignorar futuras alertas legítimas.

## Recomendación

Implementar un mecanismo de deduplicación: antes de enviar la notificación por cada elemento, verificar si ya fue notificado hoy (e.g., usando una tabla auxiliar o un campo de timestamp en el registro). Alternativamente, almacenar en caché los IDs notificados durante la sesión del día.

## Trazabilidad al test manual

- Caso: `cases/CP-HU05-15.md` → ejecución manual con dos invocaciones consecutivas.
- No hay test automatizado para este caso ya que requiere verificación del log entre ejecuciones (estado externo al comando).
