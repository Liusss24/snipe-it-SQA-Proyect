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
| CP-HU01-16  | Bloqueo de acceso sin permisos al formulario de creación    | Sistema     | Automated  | Alta     |
| CP-HU01-17  | Validación de campo obligatorio Location vacío              | Sistema     | Automated  | Alta     |
| CP-HU01-18  | Bloqueo de creación con ubicación inexistente               | Integración | Automated  | Alta     |
| CP-HU01-19  | Registro de creación en el historial de acciones            | Integración | Automated  | Media    |
| CP-HU01-20  | Sanitización del campo Asset Name ante entrada tipo script  | Sistema     | Automated  | Media    |

Los 10 casos son automatizados (Python 3.14 + pytest + Playwright).

### Resultado de ejecución (2026-05-30)

| Caso        | Resultado | Nota                                                          |
|-------------|-----------|--------------------------------------------------------------|
| CP-HU01-01  | ✅ Pass    | Activo creado con Ready to Deploy                             |
| CP-HU01-02  | ⚠️ XFail   | **DEF-US01-01**: Asset Name limitado a 191, no 255 (defecto) |
| CP-HU01-02b | ✅ Pass    | Caso complementario: valida el límite real de 191            |
| CP-HU01-03  | ✅ Pass    | Serial duplicado rechazado (requiere `unique_serial`)        |
| CP-HU01-04  | ✅ Pass    | No permite guardar sin Status Label                          |
| CP-HU01-05  | ✅ Pass    | Activo visible y consistente en el listado                   |

**Hallazgos / defectos (CP-HU01-01 a CP-HU01-05):**
- **DEF-US01-01** (`evidence/DEF-US01-01_asset_name_length.md`): el campo Asset
  Name tiene `maxlength=191` (columna `varchar(191)`); el Plan asume 255. El test
  CP-HU01-02 se marca `xfail(strict)`; CP-HU01-02b documenta el límite real.
- **Hallazgo de configuración (CP-HU01-03)**: la unicidad de serial depende del
  ajuste `unique_serial`, desactivado por defecto en Snipe-IT.

**Resultado de ejecución CP-HU01-16 a CP-HU01-20 — pendiente**

| Caso        | Resultado | Nota |
|-------------|-----------|------|
| CP-HU01-16  | _Pendiente_ | |
| CP-HU01-17  | _Pendiente_ | xfail previsto (DEF-US01-17) |
| CP-HU01-17b | _Pendiente_ | Caso complementario |
| CP-HU01-18  | _Pendiente_ | |
| CP-HU01-19  | _Pendiente_ | |
| CP-HU01-20  | _Pendiente_ | |

**Hallazgos / defectos (CP-HU01-16 a CP-HU01-20):**
- **DEF-US01-17** (`evidence/DEF-US01-17_location_no_obligatorio.md`): el campo
  Default Location no es obligatorio en Snipe-IT v8. El Plan asume que es requerido.
  CP-HU01-17 se marca `xfail(strict)`; CP-HU01-17b documenta el comportamiento real.

## Folder structure

```
US01-TestCases/
├── README.md
├── requirements.txt
├── pytest.ini
├── .env / .env.example
├── conftest.py            ← fixtures: browser, auth, noperm, datos maestros, unique_serial
├── pages/                 ← Page Object Models
│   ├── login_page.py
│   ├── asset_create_page.py
│   ├── asset_list_page.py
│   └── asset_detail_page.py       ← CP-HU01-19, CP-HU01-20
├── automated/
│   ├── test_hu01_01_02_create_asset_valid.py
│   ├── test_hu01_03_04_create_asset_negative.py
│   ├── test_hu01_05_integration.py
│   ├── test_hu01_16_permisos.py             ← CP-HU01-16
│   ├── test_hu01_17_18_location_negative.py ← CP-HU01-17, CP-HU01-17b, CP-HU01-18
│   └── test_hu01_19_20_historial_xss.py     ← CP-HU01-19, CP-HU01-20
├── cases/                 ← CP-HU01-01.md … CP-HU01-05.md, CP-HU01-16.md … CP-HU01-20.md
├── evidence/
│   ├── DEF-US01-17_location_no_obligatorio.md
│   └── .gitkeep
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
