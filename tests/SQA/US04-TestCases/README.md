# US04 – License Checkout: Test Cases

## User Story

**US04:** As a manager, I want to check out a license to a user so that the
license seat counters update correctly and the assignment is reflected across the
application.

## Test cases included

| ID          | Name                                                       | Type        | Execution  | Priority |
|-------------|------------------------------------------------------------|-------------|------------|----------|
| CP-HU04-01  | Checkout exitoso con cupos disponibles                      | Sistema     | Automated  | Alta     |
| CP-HU04-02  | Checkout exitoso con último cupo disponible                 | Sistema     | Automated  | Alta     |
| CP-HU04-03  | Licencia sin cupos no permite checkout                      | Sistema     | Automated  | Alta     |
| CP-HU04-04  | Intento forzado de checkout sin cupos muestra advertencia   | Sistema     | Automated  | Media    |
| CP-HU04-05  | Validación del campo obligatorio "Checkout to" vacío        | Sistema     | Automated  | Alta     |
| CP-HU04-06  | Cancelación del checkout antes de confirmar                 | Sistema     | Automated  | Media    |
| CP-HU04-07  | Usuario sin permisos no puede hacer checkout                | Sistema     | Automated  | Alta     |
| CP-HU04-08  | Usuario no autenticado no puede acceder al flujo            | Sistema     | Automated  | Media    |
| CP-HU04-09  | Persistencia visual de contadores tras refrescar            | Sistema     | Automated  | Media    |
| CP-HU04-10  | Prevención de doble envío del checkout                      | Sistema     | Automated  | Alta     |
| CP-HU04-11  | Checkout exitoso se refleja en el perfil del usuario        | Integración | Automated  | Alta     |
| CP-HU04-12  | Checkout bloqueado no se refleja en el perfil               | Integración | Automated  | Media    |
| CP-HU04-13  | Consistencia entre detalle y listado tras checkout          | Integración | Automated  | Media    |
| CP-HU04-14  | Consistencia del estado "No Seats Available" en vistas      | Integración | Automated  | Alta     |
| CP-HU04-15  | Usabilidad y navegación por teclado del flujo de checkout   | Sistema     | **Manual** | Media    |

## Folder structure

```
US04-TestCases/
├── README.md              ← this file
├── requirements.txt       ← Python dependencies
├── pytest.ini             ← pytest configuration
├── .env.example           ← environment variables template
├── conftest.py            ← shared fixtures (browser, auth, test data)
├── pages/                 ← Page Object Models
│   ├── login_page.py
│   ├── license_list_page.py
│   ├── license_detail_page.py
│   ├── checkout_page.py
│   └── user_profile_page.py
├── automated/             ← pytest test files (one per test group)
│   ├── test_hu04_01_02_checkout_basic.py
│   ├── test_hu04_03_04_checkout_no_seats.py
│   ├── test_hu04_05_06_checkout_validation.py
│   ├── test_hu04_07_08_checkout_permissions.py
│   ├── test_hu04_09_10_checkout_persistence.py
│   └── test_hu04_11_14_checkout_integration.py
├── cases/                 ← Documented test cases (Markdown)
│   ├── CP-HU04-01.md … CP-HU04-15.md
├── evidence/              ← Screenshots and logs per execution
└── reports/               ← Execution summary reports
```

## Prerequisites

| Requirement         | Version / value              |
|---------------------|------------------------------|
| Python              | 3.12                         |
| pytest              | ≥ 8.0                        |
| pytest-playwright   | ≥ 0.5                        |
| Playwright browsers | Chromium (via `playwright install`) |
| Snipe-IT instance   | Running locally or accessible via network |

## Environment setup

```bash
# 1. Copy the environment template
cp .env.example .env

# 2. Edit .env with your local values
#    (base URL, admin credentials, API token)

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser binaries
playwright install chromium
```

## Running the tests

```bash
# All automated US04 tests
pytest automated/ -v

# Single test group
pytest automated/test_hu04_01_02_checkout_basic.py -v

# With HTML report
pytest automated/ -v --html=reports/us04_report.html --self-contained-html

# With screenshot on failure (configured in conftest.py)
pytest automated/ -v --screenshot=only-on-failure --output=evidence/
```

## Naming conventions

| Artifact      | Pattern                                    | Example                                  |
|---------------|--------------------------------------------|------------------------------------------|
| Evidence file | `YYYY-MM-DD_CP-HU04-XX_description.png`    | `2026-05-30_CP-HU04-01_checkout_ok.png`  |
| Report file   | `YYYY-MM-DD_US04_execution_report.html`    | `2026-05-30_US04_execution_report.html`  |

## Manual test

**CP-HU04-15** must be executed manually. See [`cases/CP-HU04-15.md`](cases/CP-HU04-15.md)
for the detailed steps, observations, and evidence fields to complete.
