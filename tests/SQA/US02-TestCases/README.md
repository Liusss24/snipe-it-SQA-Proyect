# US02 – Asset Checkout: Test Cases

## User Story

**US02:** As a manager, I want to check out an asset to a user so that the asset's
status changes to Deployed, the assignment is reflected in the user's profile, and the
action is recorded in the system audit log.

## Test cases

| ID         | Title                                                                 | Type                  | Execution   | Priority |
|------------|-----------------------------------------------------------------------|-----------------------|-------------|----------|
| CP-HU02-01 | Asignación exitosa de activo disponible a usuario válido              | Integración           | Automated   | Alta     |
| CP-HU02-02 | Cambio de estado del activo de Ready to Deploy a Deployed             | Integración           | Automated   | Alta     |
| CP-HU02-03 | Registro de fecha y hora en el campo Last Checkout                    | Integración           | Automated   | Alta     |
| CP-HU02-04 | Registro del checkout en el historial de acciones del activo          | Integración           | Automated   | Alta     |
| CP-HU02-05 | Validación visual del flujo completo de checkout exitoso              | Sistema               | **Manual**  | Alta     |
| CP-HU02-06 | Validación visual de bloqueo de checkout para activo ya asignado      | Sistema               | **Manual**  | Alta     |
| CP-HU02-07 | Intento de checkout directo sobre activo ya desplegado                | Integración / Seg.    | Automated   | Alta     |
| CP-HU02-08 | Activo asignado visible en el perfil del usuario                      | Integración / Sistema | Automated   | Alta     |
| CP-HU02-09 | Checkout sin seleccionar destinatario                                 | Integración           | Automated   | Alta     |
| CP-HU02-10 | Checkout con usuario inexistente (ID inválido)                        | Integración           | Automated   | Alta     |
| CP-HU02-11 | Checkout hacia usuario inactivo                                       | Integración           | Automated   | Media    |
| CP-HU02-12 | Checkout sobre activo inexistente                                     | Integración           | Automated   | Media    |
| CP-HU02-13 | Checkout sobre activo con estado no desplegable                       | Integración           | Automated   | Alta     |
| CP-HU02-14 | Checkout por usuario sin permisos                                     | Integración           | Automated   | Alta     |
| CP-HU02-15 | Prevención de doble asignación (dos checkouts consecutivos)           | Integración           | Automated   | Alta     |

## Folder structure

```
US02-TestCases/
├── README.md              ← this file
├── composer.json          ← PHP dependencies (Pest, Guzzle, phpdotenv)
├── phpunit.xml            ← Pest/PHPUnit configuration
├── bootstrap.php          ← loads .env and vendor/autoload.php
├── .env.example           ← environment variables template
├── .env                   ← real secrets (GIT-IGNORED — never commit)
├── Helpers/
│   ├── ApiClient.php      ← api() HTTP wrapper with 429 retry
│   ├── Fixtures.php       ← MasterData class, create_user/asset, checkout, etc.
│   └── DbHelper.php       ← direct MariaDB queries via docker exec (CP-HU02-04)
├── automated/             ← Pest test files
│   ├── CP_HU02_01_02_checkout_basico.php
│   ├── CP_HU02_03_04_auditoria.php
│   ├── CP_HU02_07_double_checkout_directo.php
│   ├── CP_HU02_08_perfil_usuario.php
│   ├── CP_HU02_09_10_destinatario_invalido.php
│   ├── CP_HU02_11_12_recurso_invalido.php
│   ├── CP_HU02_13_estado_no_desplegable.php
│   ├── CP_HU02_14_sin_permisos.php
│   └── CP_HU02_15_prevencion_doble_asignacion.php
├── cases/                 ← Documented test cases (Markdown)
│   └── CP-HU02-01.md … CP-HU02-15.md
├── evidence/              ← Screenshots and defect reports
└── reports/               ← Execution summary reports
```

## Prerequisites

| Requirement         | Version / value                          |
|---------------------|------------------------------------------|
| PHP                 | 8.3.x                                    |
| Composer            | ≥ 2.x                                    |
| Pest                | ^3.0 (installed via composer)            |
| Guzzle              | ^7.0 (installed via composer)            |
| Snipe-IT instance   | Running at `http://localhost:8000`       |
| Docker              | Running (DB container `snipeit-db-1`)    |

## Environment setup

```powershell
# 1. Enter the US02 folder
cd tests/SQA/US02-TestCases

# 2. Copy the environment template and fill in your values
cp .env.example .env
# Edit .env: set SNIPEIT_API_TOKEN, SNIPEIT_NOPERM_TOKEN, SNIPEIT_DB_PASS

# 3. Install PHP dependencies
composer install

# 4. Verify Snipe-IT is reachable
curl -s -H "Authorization: Bearer <YOUR_TOKEN>" -H "Accept: application/json" ^
     http://localhost:8000/api/v1/statuslabels?limit=1
# JSON => OK.  HTML / redirect to /setup => DB down or stale cache (see project-structure.md)
```

### Generating the SNIPEIT_NOPERM_TOKEN (viewer user)

Needed for CP-HU02-14. Run inside the app container:

```bash
docker exec snipeit-app-1 bash -c 'cat > /tmp/gen_viewer_token.php << PHPEOF
<?php
$user = App\Models\User::where("username", "viewer")->first();
$token = $user->createToken("SQA-Tests-Viewer");
echo "TOKEN:" . $token->accessToken;
PHPEOF
php /var/www/html/artisan tinker --execute="require '"'"'/tmp/gen_viewer_token.php'"'"';"'
```

## Running the tests

```powershell
# All automated US02 tests
./vendor/bin/pest automated/

# With verbose test names
./vendor/bin/pest automated/ --testdox

# Single file
./vendor/bin/pest automated/CP_HU02_01_02_checkout_basico.php

# By group (e.g. only integration/positive tests)
./vendor/bin/pest automated/ --group=integracion,positivos

# With coverage (requires xdebug or pcov)
./vendor/bin/pest automated/ --coverage
```

## Naming conventions

| Artifact        | Pattern                                      | Example                                     |
|-----------------|----------------------------------------------|---------------------------------------------|
| Evidence file   | `YYYY-MM-DD_CP-HU02-XX_description.png`      | `2026-05-31_CP-HU02-05_checkout_ok.png`     |
| Defect file     | `DEF-US02-NN_<short>.md`                     | `DEF-US02-01_asset_already_checked_out.md`  |
| Report file     | `YYYY-MM-DD_US02_execution_report.txt`       | `2026-05-31_US02_execution_report.txt`      |

## Manual tests

**CP-HU02-05** and **CP-HU02-06** must be executed manually in Chrome.
See their respective `.md` files in `cases/` for detailed steps, evidence requirements, and fields to fill in after execution.

## Results — Ejecución 2026-05-31

**Suite automatizada:** 11 passed, 2 skipped (defectos), 0 failed — 43 assertions en 43 s.

| ID         | Status  | Notes                                              |
|------------|---------|----------------------------------------------------|
| CP-HU02-01 | ✅ Pass  | Checkout exitoso, mensaje confirmado               |
| CP-HU02-02 | ✅ Pass  | Estado cambia a `deployed`                         |
| CP-HU02-03 | ✅ Pass  | `last_checkout` registrado en rango ±60 s          |
| CP-HU02-04 | ✅ Pass  | Registro en `action_logs` verificado vía DB        |
| CP-HU02-05 | ✅ Pass  | Flujo completo de checkout visual exitoso (manual) |
| CP-HU02-06 | ✅ Pass  | Bloqueo de checkout para activo ya asignado(manual)|
| CP-HU02-07 | ✅ Pass  | Segundo checkout rechazado; asignación original OK |
| CP-HU02-08 | ✅ Pass  | Activo visible en perfil del usuario               |
| CP-HU02-09 | ✅ Pass  | Sin destinatario → rechazado, activo sin cambios   |
| CP-HU02-10 | ✅ Pass  | Usuario inexistente → rechazado                    |
| CP-HU02-11 | ❌ Fail  | DEF-US02-01: permite checkout a usuario inactivo   |
| CP-HU02-12 | ❌ Fail  | DEF-US02-02: retorna HTTP 200 para asset inexistente|
| CP-HU02-13 | ✅ Pass  | Activo Pending → checkout rechazado                |
| CP-HU02-14 | ✅ Pass  | Viewer → HTTP 403                                  |
| CP-HU02-15 | ✅ Pass  | Solo primer checkout aceptado                      |

### Defectos encontrados

| ID          | Severidad | Descripción breve                                        |
|-------------|-----------|----------------------------------------------------------|
| DEF-US02-01 | Media     | Checkout permitido a usuario con `activated=false`       |
| DEF-US02-02 | Alta      | Checkout de asset inexistente retorna HTTP 200 en vez de 404 |
