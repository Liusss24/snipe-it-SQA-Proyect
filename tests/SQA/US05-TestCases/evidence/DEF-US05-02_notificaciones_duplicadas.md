# DEF-US05-02 – El sistema envía notificaciones duplicadas en ejecuciones repetidas

## Defect ID
DEF-US05-02

## Related test case
CP-HU05-15

## Severity
Medium

## Priority
Medium

## Snipe-IT version
v8.4.0 (build 21690)

## Description

El comando `snipeit:expiring-alerts` no implementa ningún mecanismo de
deduplicación de notificaciones. Cada ejecución genera y envía correos para
**todos** los elementos dentro del umbral, sin verificar si ya fueron
notificados en el período actual.

Esto viola el criterio de aceptación CA-02 de HU-05, que exige que no se
reenvíen notificaciones duplicadas para el mismo elemento sin cambios.

## Evidence

Verificado con `MAIL_MAILER=log` (correos registrados en `storage/logs/laravel.log`):

| Ejecución | Entradas `To:` en log |
|---|---|
| 1ra ejecución | 2 (1 de activos + 1 de licencias) |
| 2da ejecución (sin cambios) | 4 (+2 correos idénticos) |

### Pasos para reproducir

```powershell
# 1. Habilitar log de correos
docker exec proyecto_qa-app-1 sh -c "sed -i 's/LOG_LEVEL=warning/LOG_LEVEL=debug/' /var/www/html/.env"
docker exec proyecto_qa-app-1 php artisan config:clear

# 2. Limpiar log
docker exec proyecto_qa-app-1 sh -c "echo '' > /var/www/html/storage/logs/laravel.log"

# 3. Primera ejecución
docker exec proyecto_qa-app-1 php artisan snipeit:expiring-alerts

# 4. Contar correos
docker exec proyecto_qa-app-1 grep -c "To: qa-alerts@example.test" /var/www/html/storage/logs/laravel.log
# → 2

# 5. Segunda ejecución SIN modificar datos
docker exec proyecto_qa-app-1 php artisan snipeit:expiring-alerts

# 6. Contar de nuevo
docker exec proyecto_qa-app-1 grep -c "To: qa-alerts@example.test" /var/www/html/storage/logs/laravel.log
# → 4  (DEFECTO: 2 correos adicionales duplicados)
```

## Root cause

`SendExpirationAlerts::handle()` no mantiene estado entre ejecuciones. Cada vez
que el comando corre consulta la BD, encuentra los mismos elementos y envía correo
sin comprobar si ya notificó en las últimas 24 horas.

## Expected behavior

El sistema debería mantener un registro de las notificaciones enviadas (por ejemplo
en una tabla `alert_logs` o usando `cache`) y omitir el reenvío si el elemento ya
fue notificado en el período de configuración.

## Impact

En producción con el scheduler diario (`0 0 * * *`) el impacto es controlado
(1 correo por elemento por día). Sin embargo, si el cron se configura con mayor
frecuencia por error, o si el administrador ejecuta el comando manualmente, se
genera saturación de la bandeja de entrada.

## Test status
- Test CP-HU05-15 ejecutado manualmente — resultado: FAIL.
