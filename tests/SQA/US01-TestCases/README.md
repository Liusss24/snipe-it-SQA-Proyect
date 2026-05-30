# US01 – Creación de Activos: Test Cases

## User Story

**US01:** Como usuario con permisos, quiero crear activos desde Assets > Create New
de forma que el activo quede registrado con su modelo, estado y ubicación correctos
y sea visible en el listado general.

## Test cases included

| ID          | Name                                                        | Type        | Execution  | Priority |
|-------------|-------------------------------------------------------------|-------------|------------|----------|
| CP-HU01-01  | Creación exitosa con estado Ready to Deploy                 | Sistema     | Automated  | Alta     |
| CP-HU01-02  | Creación exitosa con Asset Name de 255 caracteres           | Sistema     | Automated  | Media    |
| CP-HU01-03  | Bloqueo de creación con serial duplicado                    | Sistema     | Automated  | Alta     |
| CP-HU01-04  | No permite guardar sin Status Label                         | Sistema     | Automated  | Alta     |
| CP-HU01-05  | El activo creado aparece en el listado de Assets            | Integración | Automated  | Alta     |

Los 5 casos son automatizados (Python 3.12 + pytest + Playwright).

## Folder structure

```
US01-TestCases/
├── README.md
├── requirements.txt
├── pytest.ini
├── .env / .env.example
├── conftest.py            ← fixtures: browser, auth, datos maestros, unique_serial
├── pages/                 ← Page Object Models
│   ├── login_page.py
│   ├── asset_create_page.py
│   └── asset_list_page.py
├── automated/
│   ├── test_hu01_01_02_create_asset_valid.py
│   ├── test_hu01_03_04_create_asset_negative.py
│   └── test_hu01_05_integration.py
├── cases/                 ← CP-HU01-01.md … CP-HU01-05.md
├── evidence/
└── reports/
```

## Prerequisites

| Requirement         | Version / value                       |
|---------------------|---------------------------------------|
| Python              | 3.12+                                 |
| pytest-playwright   | ≥ 0.5 (Chromium vía `playwright install`) |
| Snipe-IT            | Instancia local en `SNIPEIT_BASE_URL` |
| Docker              | Requerido sólo por CP-HU01-03 (ajuste `unique_serial`) |

Los datos maestros (categoría **Laptops**, modelo **Dell Latitude 5420**,
ubicación **Oficina Central**) se crean automáticamente vía API en el fixture
`asset_prereqs` y se eliminan al final de la sesión. El Status Label
**Ready to Deploy** se reutiliza del que ya trae Snipe-IT.

## Nota sobre CP-HU01-03 (serial duplicado)

Snipe-IT **no obliga seriales únicos por defecto** (`unique_serial = 0`). El
fixture `unique_serial_enabled` activa el ajuste en la base de datos antes de la
prueba y restaura el valor original al terminar, usando las credenciales de BD
definidas en `.env` (`SNIPEIT_DB_*`). Si Docker/BD no está disponible, el test
hace *skip* con un mensaje claro en lugar de fallar.

## Environment setup

```bash
cp .env.example .env          # editar con valores reales
pip install -r requirements.txt
playwright install chromium
```

## Running the tests

```bash
pytest automated/ -v
pytest automated/test_hu01_01_02_create_asset_valid.py -v
pytest automated/ -v --html=reports/2026-05-30_US01_execution_report.html --self-contained-html
```

## Naming conventions

| Artifact            | Pattern                                        | Example                                   |
|---------------------|------------------------------------------------|-------------------------------------------|
| Test file           | `test_huXX_NN_MM_<desc>.py`                    | `test_hu01_01_02_create_asset_valid.py`   |
| Case doc            | `CP-HU01-NN.md`                                | `CP-HU01-01.md`                           |
| Evidence            | `YYYY-MM-DD_CP-HU01-NN_<desc>.png`             | `2026-05-30_CP-HU01-01_created.png`       |
| Report              | `YYYY-MM-DD_US01_execution_report.html`        | `2026-05-30_US01_execution_report.html`   |
