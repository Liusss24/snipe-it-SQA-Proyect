# US05 – Alertas por Vencimiento y Garantía: Test Cases

## User Story

**US05:** Como administrador del sistema, quiero recibir alertas automáticas cuando
las licencias y garantías de activos estén próximas a vencer, de forma que pueda
tomar acciones preventivas antes de que ocurra el vencimiento.

## Test cases included

| ID          | Name                                                              | Type        | Execution  | Priority |
|-------------|-------------------------------------------------------------------|-------------|------------|----------|
| CP-HU05-01  | Alerta visible para licencia con vencimiento dentro de 30 días    | Sistema     | Automated  | Alta     |
| CP-HU05-02  | Licencia que vence exactamente en el día límite genera alerta      | Sistema     | Automated  | Alta     |
| CP-HU05-03  | Licencia fuera del umbral de vencimiento no genera alerta          | Sistema     | Automated  | Media    |
| CP-HU05-04  | Alerta por garantía de activo próxima a vencer                     | Sistema     | Automated  | Alta     |
| CP-HU05-05  | Garantía que vence hoy es incluida como alerta vigente             | Sistema     | Automated  | Alta     |
| CP-HU05-06  | Activo sin fecha de compra no genera alerta de garantía            | Sistema     | Automated  | Media    |
| CP-HU05-07  | Activo sin meses de garantía no genera alerta de garantía          | Sistema     | Automated  | Media    |
| CP-HU05-08  | Activo con fecha EOL próxima genera alerta                         | Integración | Automated  | Alta     |
| CP-HU05-09  | Activo con garantía y EOL próximos no aparece duplicado            | Integración | Automated  | Media    |
| CP-HU05-10  | Activo archivado no genera alerta de vencimiento                   | Sistema     | Automated  | Media    |
| CP-HU05-11  | Alertas deshabilitadas impiden envío de correo                     | Sistema     | Automated  | Alta     |
| CP-HU05-12  | Sin correo de alerta configurado no se envía notificación          | Sistema     | Automated  | Alta     |
| CP-HU05-13  | Proceso programado diario ejecuta revisión de alertas              | Integración | Automated  | Alta     |
| CP-HU05-14  | Claridad y utilidad de la información mostrada en la alerta        | Exploratoria| **Manual** | Media    |
| CP-HU05-15  | No se generan notificaciones duplicadas en ejecuciones repetidas   | Integración | **Manual** | Alta     |

### Resultado de ejecución (2026-06-04)

| Caso        | Resultado   | Nota                                                                          |
|-------------|-------------|-------------------------------------------------------------------------------|
| CP-HU05-01  | ✅ Pass     | LIC-HU05-01 aparece en el output con fecha y días restantes                   |
| CP-HU05-02  | ✅ Pass     | Límite superior (día 30) es inclusivo — confirmado                            |
| CP-HU05-03  | ✅ Pass     | Licencia a 45 días correctamente excluida                                     |
| CP-HU05-04  | ✅ Pass     | Activo con garantía próxima aparece en alertas                                |
| CP-HU05-05  | ⚠️ XFail   | **DEF-US05-01**: Snipe-IT excluye garantías que vencen hoy (datetime vs fecha)|
| CP-HU05-06  | ✅ Pass     | Activo sin purchase_date correctamente excluido                               |
| CP-HU05-07  | ✅ Pass     | Activo sin warranty_months correctamente excluido                             |
| CP-HU05-08  | ✅ Pass     | Activo con EOL en 5 días aparece en alertas                                   |
| CP-HU05-09  | ✅ Pass     | Activo con garantía + EOL aparece exactamente 1 vez (sin duplicados)          |
| CP-HU05-10  | ✅ Pass     | Activo archivado correctamente excluido                                       |
| CP-HU05-11  | ✅ Pass     | Output: "Alerts are disabled in the settings. No mail will be sent"           |
| CP-HU05-12  | ✅ Pass     | Output: "Could not send email. No alert email configured in settings"         |
| CP-HU05-13  | ✅ Pass     | `schedule:list` confirma cron `0 0 * * *` para `snipeit:expiring-alerts`      |
| CP-HU05-14  | ✅ Pass     | Manual: alerta visible, clara, con nombre/fecha/días restantes                |
| CP-HU05-15  | ❌ Fail     | **DEF-US05-02**: Duplica notificaciones en cada ejecución (4 correos vs 2)    |

**Hallazgos / defectos:**
- **DEF-US05-01** (`evidence/DEF-US05-01_garantia_dia_actual.md`): `getExpiringWarrantyOrEol()`
  usa `Carbon::now()` (datetime) en lugar de `Carbon::today()` (fecha). Las garantías que
  vencen a medianoche quedan fuera del rango. CP-HU05-05 marcado como `xfail(strict)`.
- **DEF-US05-02** (`evidence/DEF-US05-02_notificaciones_duplicadas.md`): El comando
  `snipeit:expiring-alerts` no implementa deduplicación. Cada ejecución genera correos
  duplicados para los mismos elementos. Verificado con `MAIL_MAILER=log`.

## Folder structure

```
US05-TestCases/
├── README.md              ← este archivo
├── requirements.txt       ← dependencias Python
├── pytest.ini             ← configuración pytest
├── .env.example           ← plantilla de variables de entorno
├── conftest.py            ← fixtures: auth, seeding vía API+artisan, cleanup
├── pages/
│   ├── __init__.py
│   └── alert_settings_page.py   ← Admin > Settings > Alerts + License detail
├── automated/
│   ├── __init__.py
│   ├── test_hu05_01_03_licencias_umbral.py      ← CP-HU05-01, 02, 03
│   ├── test_hu05_04_07_garantias_activos.py     ← CP-HU05-04, 05, 06, 07
│   ├── test_hu05_08_10_eol_archivado.py         ← CP-HU05-08, 09, 10
│   └── test_hu05_11_13_config_scheduler.py      ← CP-HU05-11, 12, 13
├── cases/                 ← CP-HU05-01.md … CP-HU05-15.md
├── evidence/
│   ├── DEF-US05-01_garantia_dia_actual.md
│   └── DEF-US05-02_notificaciones_duplicadas.md
└── reports/
    └── 2026-06-04_US05_execution_report.html
```

## Architecture note – Hybrid seeding strategy

Los tests de HU05 usan una estrategia híbrida (igual que US02):
- **REST API** para crear/eliminar licencias y activos (mismo patrón que US01/US04).
- **`php artisan tinker`** para configurar alert settings (no hay endpoint API para eso).
- **`php artisan snipeit:expiring-alerts`** vía subprocess para ejecutar el pipeline
  de alertas y capturar su output en consola.

## Prerequisites

| Requirement         | Version / value                        |
|---------------------|----------------------------------------|
| Python              | 3.12+                                  |
| pytest-playwright   | ≥ 0.5 (Chromium vía `playwright install`) |
| Snipe-IT            | Instancia local en `SNIPEIT_BASE_URL`  |
| Docker              | Requerido para los comandos artisan    |
| MAIL_MAILER         | `log` (para CP-HU05-15 manual)         |

## Environment setup

```bash
cp .env.example .env      # editar con valores reales
pip install -r requirements.txt
playwright install chromium
```

## Running the tests

```bash
# Todos los tests automatizados (CP-HU05-01 a 13, excl. 05 que es xfail)
pytest automated/ -v

# Grupo específico
pytest automated/test_hu05_01_03_licencias_umbral.py -v

# Con reporte HTML
pytest automated/ -v --html=reports/2026-06-04_US05_execution_report.html --self-contained-html
```

> **CP-HU05-14 y CP-HU05-15** deben ejecutarse manualmente.
> Ver `cases/CP-HU05-14.md` y `cases/CP-HU05-15.md` para los pasos detallados.

## Naming conventions

| Artifact      | Pattern                                        | Example                                     |
|---------------|------------------------------------------------|---------------------------------------------|
| Test file     | `test_huXX_NN_MM_<desc>.py`                    | `test_hu05_01_03_licencias_umbral.py`        |
| Case doc      | `CP-HU05-NN.md`                                | `CP-HU05-01.md`                             |
| Evidence      | `YYYY-MM-DD_CP-HU05-NN_<desc>.png`             | `2026-06-04_CP-HU05-01_alert_output.png`    |
| Defect        | `DEF-US05-NN_<desc>.md`                        | `DEF-US05-01_garantia_dia_actual.md`        |
| Report        | `YYYY-MM-DD_US05_execution_report.html`        | `2026-06-04_US05_execution_report.html`     |
