# SQA Project Structure — Initialization Guide

This document explains the conventions, folder layout, and initialization steps for
any new User Story (US) test branch in this project. Use it as the entry point when
starting QA work on a new US.

## ⚠️ Disclaimer — Stack may vary per US

US01 and US04 were automated with **Python 3.12 + pytest + Playwright**, and most of this
guide assumes that stack (`conftest.py` fixtures, Page Objects, `pytest.ini`, etc.).
However, **the tool for each case is defined by `Plan de Pruebas.docx`** and may differ:
Selenium, JMeter (performance), Pest/PHPUnit (backend), or manual testing.

Before copying the Python template, **check which tool the US requires**. If it is not
Python/Playwright, adapt the structure (language, dependencies, runner) and take from this
guide only what applies cross-cutting:

- Folder/branch/commit conventions
- Case documentation (`.md` files)
- Defects workflow
- Docker environment data
- Report generation

---

## Context

- **Project:** Snipe-IT (fork – SQA analysis). The goal of this fork is to apply SQA
  and **find real defects** in Snipe-IT.
- **Repository:** `snipe-it-SQA-Proyect`
- **Main branch:** `master`
- **Pattern per US:** one dedicated Git branch named `USxx-TestCases`
- **Test Plan document:** `C:\Users\Aaron\Downloads\Plan de Pruebas.docx`
- **Report template:** `C:\Users\Aaron\Downloads\Informe de Pruebas.docx`
- **System under test:** Snipe-IT v8.4.0 (build 21690), deployed locally via Docker.
- **Completed so far (use as reference implementations):**
  - `US04-TestCases` — Checkout de Licencias: 15 cases (14 automated + 1 manual). All Pass.
  - `US01-TestCases` — Creación de Activos: 5 cases + 1 complementary. 5 Pass, 1 documented
    defect (DEF-US01-01). **Copy whichever is closest to the new US's module.**

---

## Local Snipe-IT environment (Docker)

The instance runs in two containers:

| Container       | Image                | Purpose                                  |
|-----------------|----------------------|------------------------------------------|
| `snipeit-app-1` | `snipe/snipe-it:latest` | Laravel app, exposed at `http://localhost:8000` |
| `snipeit-db-1`  | `mariadb:11.4.7`     | Database `snipeit_db`                     |

**Credentials & access (already provisioned, stored in each US's `.env`):**

| Item                | Value                                            |
|---------------------|--------------------------------------------------|
| Admin UI login      | `admin` / `SQA-Admin2026!`                        |
| DB (app user)       | user `snipeit_user`, db `snipeit_db` (pass in `.env` as `SNIPEIT_DB_PASS`) |
| API token           | Bearer token in `.env` as `SNIPEIT_API_TOKEN`     |
| No-permissions user | `viewer` / `SQA-Viewer2026!` (for permission tests) |

**DB access uses the `mariadb` client, NOT `mysql`** (the image ships only `mariadb`):

```bash
docker exec snipeit-db-1 mariadb -u snipeit_user -p"<DB_PASS>" snipeit_db -N -s -e "SELECT ...;"
```

### Generating / regenerating the API token

Tokens are Passport OAuth tokens. Generate one inside the app container via `artisan tinker`.
The artisan path is `/var/www/html/artisan` — **Git Bash mangles absolute paths**, so run it
through `bash -c` inside the container (writing a temp PHP file avoids quoting hell):

```bash
docker exec snipeit-app-1 bash -c 'cat > /tmp/gen_token.php << PHPEOF
<?php
$user = App\Models\User::find(1);
$token = $user->createToken("SQA-Tests");
echo "TOKEN:" . $token->accessToken;
PHPEOF
php /var/www/html/artisan tinker --execute="require '/tmp/gen_token.php';"'
```

### Docker gotchas (observed during US01/US04)

- **`snipeit-db-1` can stop independently** of the app. Symptom: the API redirects to
  `/setup` or `/login` and returns HTML instead of JSON. Fix:
  ```bash
  docker start snipeit-db-1
  docker exec snipeit-app-1 bash -c 'php /var/www/html/artisan cache:clear'
  ```
- After any restart, **clear the cache** (`cache:clear`, and `config:clear` if needed) before
  trusting the API again.
- A token that suddenly 302-redirects usually means the DB is down or the cache is stale —
  it does **not** necessarily mean the token expired.

---

## Branch & git conventions

```bash
# Create a new branch for a US
git checkout -b US05-TestCases

# Commits must be under the project owner's name (Aarón Líos Cubillo / Liusss24).
# .claude/ is listed in .gitignore — no AI traces in the remote repo.
```

---

## Folder layout (one folder per US inside tests/SQA/)

```
tests/
├── SQA/                          ← project-wide SQA assets (existing)
│   ├── README.md
│   ├── .gitignore                ← ignores /evidence/* and /reports/* EXCEPT *.docx + gen_informe.js
│   ├── cases/
│   │   └── manual-test-case-template.md   ← base template for all case .md
│   ├── checklists/
│   ├── evidence/
│   ├── reports/
│   │   ├── gen_informe.js        ← docx-js generator for the Informe de Pruebas (versioned)
│   │   └── Informe de Pruebas - US01 y US04.docx   ← formal deliverable (versioned)
│   │
│   ├── US01-TestCases/           ← reference impl: entity creation (forms)
│   ├── US04-TestCases/           ← reference impl: action/flow (checkout)
│   │
│   └── USxx-TestCases/           ← NEW folder per US (copy the closest reference above)
│       ├── README.md             ← index of cases, setup, run instructions, results table
│       ├── requirements.txt      ← Python deps (pytest, pytest-playwright, pytest-html, dotenv, requests)
│       ├── pytest.ini            ← markers (sistema/integracion/negative/high/medium), --output, screenshots
│       ├── .env.example          ← env template (committed)
│       ├── .env                  ← real secrets (GIT-IGNORED — never commit)
│       ├── conftest.py           ← _api helper (429-retry), browser/auth fixtures, data fixtures
│       │
│       ├── pages/                ← Page Object Models (login_page.py + one per UI page)
│       │   └── __init__.py
│       ├── automated/            ← test_huXX_NN_MM_<description>.py  (+ __init__.py)
│       ├── cases/                ← CP-HUxx-NN.md (one per case)
│       ├── evidence/             ← screenshots, DEF-USxx-NN_*.md  (+ .gitkeep)
│       └── reports/              ← YYYY-MM-DD_USxx_execution_report.html  (+ .gitkeep)
│
├── Feature/                      ← Laravel/PHPUnit tests (existing, DO NOT modify)
└── Unit/                         ← Laravel/PHPUnit tests (existing, DO NOT modify)
```

---

## Tools per test type

> La herramienta de cada caso la dicta el `Plan de Pruebas.docx`. La tabla siguiente es
> orientativa; **US01 y US04 usaron la fila de Python + Playwright**, pero otras US pueden
> caer en cualquiera de las demás filas (o combinar varias).

| Test type        | Tools                                   | Notes                              |
|------------------|-----------------------------------------|------------------------------------|
| UI / Sistema     | Python 3.12 + pytest + Playwright       | Stack usado en US01/US04. Chromium, 1920×1080 |
| UI / Integración | Python 3.12 + pytest + Playwright       | Stack usado en US01/US04. Cross-module checks |
| UI (alternativa) | Selenium WebDriver (Python u otro)      | Si el plan lo pide en vez de Playwright |
| Manual           | Markdown case file + manual execution   | Fill "Actual result" and evidence  |
| Performance      | JMeter                                  | Proyecto `.jmx` aparte; no usa pytest |
| Unit / Backend   | Pest / PHPUnit (PHP)                     | `php artisan test --testsuite=...` |

Si la US **no** usa Python/Playwright, las secciones de esta guía sobre `conftest.py`,
Page Objects, `pytest.ini` y los patrones de Select2/AJAX **no aplican**; usá en su lugar la
estructura propia de la herramienta correspondiente, manteniendo igual el resto de convenciones.

---

## Environment setup for a new US

```bash
# 1. Create the US folder by copying the CLOSEST existing US as a template:
#    - module about creating/editing entities (forms)  -> copy US01-TestCases
#    - module about an action/flow on an entity (checkout, etc.) -> copy US04-TestCases
cp -r tests/SQA/US01-TestCases tests/SQA/USxx-TestCases

# 2. Copy the .env (same instance, reuse credentials/token/DB vars)
cp tests/SQA/US01-TestCases/.env tests/SQA/USxx-TestCases/.env

# 3. Update README.md, cases/, pages/ and automated/ with new test IDs and logic
#    Delete fixtures/pages that don't apply; rename test files to test_huXX_*.

# 4. Install Python deps (once per machine is enough)
cd tests/SQA/USxx-TestCases
pip install -r requirements.txt
playwright install chromium

# 5. Verify Snipe-IT is up and the API token is valid:
curl -s -H "Authorization: Bearer <TOKEN>" -H "Accept: application/json" \
     http://localhost:8000/api/v1/statuslabels?limit=1
#    JSON => OK.  HTML/redirect to /setup or /login => DB down or stale cache (see Docker gotchas).
```

> Read the **"CRITICAL: Snipe-IT automation patterns"** section below before writing Page
> Objects — it captures the AJAX/Select2/collapsible-form behaviours that are not obvious.

---

## conftest.py conventions

| Variable                    | Source        | Purpose                                   |
|-----------------------------|---------------|-------------------------------------------|
| `SNIPEIT_BASE_URL`          | `.env`        | Base URL, no trailing slash               |
| `SNIPEIT_ADMIN_USERNAME`    | `.env`        | Admin login for `auth_page` fixture       |
| `SNIPEIT_ADMIN_PASSWORD`    | `.env`        | Admin password                            |
| `SNIPEIT_API_TOKEN`         | `.env`        | Bearer token for test-data setup via API  |
| `SNIPEIT_NOPERM_USERNAME`   | `.env`        | User with restricted permissions          |
| `SNIPEIT_NOPERM_PASSWORD`   | `.env`        | Password for the restricted user          |
| `SNIPEIT_DB_CONTAINER`      | `.env`        | DB container name (`snipeit-db-1`) — only if the US toggles settings via DB |
| `SNIPEIT_DB_NAME`           | `.env`        | `snipeit_db`                              |
| `SNIPEIT_DB_USER`           | `.env`        | `snipeit_user`                            |
| `SNIPEIT_DB_PASS`           | `.env`        | DB password (for `mariadb` client calls)   |

Key fixtures to reuse or adapt:

- `page` — plain browser page (unauthenticated)
- `auth_page` — page already logged in as admin
- `noperm_page` — page logged in as restricted user (`viewer`)
- `base_url` — session-scoped base URL string

Key API helpers in `conftest.py` (import them in test files: `from conftest import _api, ...`):

- `_api(method, endpoint, data=None)` — REST client with **automatic retry on HTTP 429**
  (rate limit). Always go through this, never raw `requests`.
- Domain helpers built on `_api`, e.g. `get_free_seats()`, `get_checked_out_count()`,
  `user_has_license()`, `find_assets_by_serial()`. Add equivalent read-helpers for the new US.

Test-data fixtures must **create and clean up** resources (yield + DELETE via API). Lessons:

- **Use unique usernames** (`first.last.<uuid>`) — Snipe-IT enforces username uniqueness and
  leftover users from a crashed run will collide. Same idea for any unique field.
- **Space out creations** (`time.sleep(1.2)`) to avoid the API rate limit during setup.
- If a `POST` returns no `payload.id`, `pytest.skip(...)` with the response body instead of
  letting a cryptic `NoneType` error propagate.
- Master data (categories, models, manufacturers, locations) that several cases share should
  be created once with a **session-scoped** fixture and torn down at the end.

---

## CRITICAL: Snipe-IT automation patterns (hard-won, reuse these)

These are non-obvious behaviours of the Snipe-IT UI that broke the first naive attempts.
**Read this before writing Page Objects for a new module.**

### 1. Assert against the REST API, not the DOM

List tables and counters (assets list, license seats, user licenses) are rendered
asynchronously by **Bootstrap Table via AJAX**. Reading them from the DOM is flaky and often
returns empty. **Treat the REST API as the source of truth** for assertions:

```python
# Instead of scraping the seats table in the DOM:
assert get_free_seats(lic_id) == 1          # GET /api/v1/licenses/{id}
assert user_has_license(user_id, lic_name)  # GET /api/v1/users/{id}/licenses
```
Use the UI (Playwright) to **perform the action**; use the API to **verify the outcome**.

### 2. Select2 fields (users, models, locations, status) load options via AJAX

Dropdowns like `assigned_user`, `model_id`, `status_id`, `rtd_location_id` are Select2 widgets
with an AJAX data source. You cannot `select_option` them directly. Inject the option and fire
the change event via jQuery/`page.evaluate()`:

```python
def _set_select2(self, select_id, value, label=""):
    self.page.evaluate(
        """([sid, val, lbl]) => {
            const s = document.getElementById(sid);
            if (!Array.from(s.options).some(o => o.value == val)) {
                s.add(new Option(lbl || val, val, true, true));  # AJAX source needs the Option created first
            }
            if (window.$ && $(s).data('select2')) { $(s).val(val).trigger('change'); }
            else { s.value = val; s.dispatchEvent(new Event('change', {bubbles: true})); }
        }""",
        [select_id, str(value), label],
    )
```

### 3. The asset-create form hides fields in a collapsible section

In the asset creation form (Snipe-IT v8), `Asset Name` and other fields live inside
`div#optional_details` (style `display:none`, "Optional Information"). Playwright sees them as
"not visible" and `fill()` times out. **Reveal collapsible sections via JS after navigating:**

```python
def _reveal_hidden_sections(self):
    self.page.evaluate("""() => {
        const opt = document.getElementById('optional_details');
        if (opt) opt.style.display = 'block';
        document.querySelectorAll('.collapse').forEach(c => {
            c.style.display = 'block'; c.classList.add('in', 'show');
        });
    }""")
```

### 4. Scope the submit button to its form

The page has a navbar search form too. A bare `button[type=submit]` may click the wrong one
(symptom seen: flash "Asset with tag not found"). Scope it:

```python
self.page.locator("form:has(select[name='assigned_to']) button[type='submit']").click()
# asset create form submit button id is #submit_button
```

### 5. Known real field selectors (verified)

| Form                | Field         | Selector                                   |
|---------------------|---------------|--------------------------------------------|
| Login               | username/pass | `input[name='username']` / `input[name='password']` |
| License checkout    | user          | Select2 `#assigned_user_select` (name `assigned_to`) |
| Asset create        | Asset Name    | `#name` (inside `#optional_details`, maxlength=191) |
| Asset create        | Asset Tag     | `#asset_tag` (name `asset_tags[1]`)        |
| Asset create        | Serial        | `input[name='serials[1]']`                 |
| Asset create        | Model         | Select2 `#model_select_id` (name `model_id`) |
| Asset create        | Status        | Select2 `#status_select_id` (name `status_id`) |
| Asset create        | Location      | Select2 `#rtd_location_id_location_select` |
| Asset create        | Submit        | `#submit_button`                           |

### 6. Settings that change validation behaviour

Some "negative" cases only make sense if a Snipe-IT setting is toggled. Manage the setting in a
fixture (read original → set → yield → restore) using the DB helper. Example seen in US01:

- **`unique_serial`** is **0 by default** → Snipe-IT allows duplicate serials. The
  duplicate-serial test must enable it first, then restore:

```python
@pytest.fixture
def unique_serial_enabled():
    original = _get_unique_serial()          # SELECT unique_serial FROM settings WHERE id=1
    if original != 1: _set_unique_serial(1)  # UPDATE settings ...
    yield
    _set_unique_serial(original)
```
If Docker/DB is unreachable, `pytest.skip(...)` rather than failing misleadingly.

### 7. Expect to find defects — document, don't force-pass

When the system genuinely deviates from the Test Plan, that is a **finding, not a test bug**.
Document it as a defect (see Defects workflow below) and mark the automated test
`@pytest.mark.xfail(reason="DEF-USxx-NN: ...", strict=True)`. Optionally add a complementary
test (`CP-...b`) that validates the system's *real* behaviour so the suite still has a green
boundary case. Real example: **DEF-US01-01** — Asset Name is `varchar(191)` / `maxlength=191`,
but the Plan assumed 255; the system truncates. `CP-HU01-02` is `xfail`, `CP-HU01-02b` verifies
the real 191 limit and passes.

---

## Test case markdown format

Follow the template at `tests/SQA/cases/manual-test-case-template.md`.
For US-specific cases, extend with these fields:

```markdown
- **ID:** CP-HUxx-NN
- **US:** HUxx
- **Type:** Sistema | Integración | Rendimiento
- **Technique:** Caja negra / Partición de equivalencia | Valores límite | etc.
- **Execution:** Automatizada | Manual
- **Assigned to:** Aarón Líos Cubillo
```

After execution, fill in **Actual result**, **Status**, and **Evidence**.

---

## Naming conventions

| Artifact            | Pattern                                         | Example                                       |
|---------------------|-------------------------------------------------|-----------------------------------------------|
| Test file           | `test_huXX_NN_MM_<description>.py`              | `test_hu04_01_02_checkout_basic.py`           |
| Case doc            | `CP-HUxx-NN.md`                                 | `CP-HU04-01.md`                               |
| Evidence screenshot | `YYYY-MM-DD_CP-HUxx-NN_<description>.png`       | `2026-05-30_CP-HU04-01_checkout_ok.png`       |
| Report file         | `YYYY-MM-DD_USxx_execution_report.html`         | `2026-05-30_US04_execution_report.html`       |

---

## Running tests

```bash
# All tests for this US
pytest automated/ -v

# Only integration tests
pytest automated/ -v -m integracion

# With HTML report saved to reports/
pytest automated/ -v --html=reports/YYYY-MM-DD_USxx_execution_report.html --self-contained-html

# Screenshots on failure land in evidence/
pytest automated/ -v --screenshot=only-on-failure --output=evidence/
```

---

## Defects workflow

When a case reveals a real system deviation:

1. Create `evidence/DEF-USxx-NN_<short>.md` with: ID, associated case, module, severity,
   priority, type, status, description, steps to reproduce, expected vs. obtained result,
   evidence, analysis, recommendation, and traceability to the automated test. (See
   `tests/SQA/US01-TestCases/evidence/DEF-US01-01_asset_name_length.md` as the reference.)
2. Mark the automated test `@pytest.mark.xfail(reason="DEF-USxx-NN: ...", strict=True)`.
3. Update the case `.md` Status to `Fail` and fill `Defect link (if fail)`.
4. Note the defect in the US `README.md` results table.

Distinguish a **defect** (system wrong vs. spec) from a **configuration finding** (e.g.
`unique_serial` off by default) — both go in the report's Defects section, ordered by test type.

---

## Report (Informe de Pruebas)

Two artifacts per cycle:

1. **HTML execution report** (auto-generated by pytest), saved in each US's `reports/`:
   `pytest automated/ --html=reports/YYYY-MM-DD_USxx_execution_report.html --self-contained-html`
2. **Informe de Pruebas (.docx)** — the formal deliverable, generated with **docx-js**.

### Generating the .docx

A reusable generator lives at `tests/SQA/reports/gen_informe.js` (docx-js). It already produces
a professional document with cover page, TOC, result tables (green/red shading per outcome),
quantitative summary, defect tables, and **code blocks in monospaced format** (Consolas, grey
background). To regenerate or extend it for more US:

```bash
cd tests/SQA/reports
NODE_PATH="$(npm root -g)" node gen_informe.js   # docx is installed globally (docx@9.x)
```

When adding a US, append its rows to the `usXXCases` arrays and add any new code excerpts.
**Take code excerpts directly from the project files** and keep CLI/code formatting (the
`codeBlock()` helper preserves line breaks and monospacing).

### Report sections (per template `Informe de Pruebas.docx`)

| Section             | Content                                                            | When |
|---------------------|--------------------------------------------------------------------|------|
| 1. Introducción     | Scope, objective, methodology, limitations                         | Final cycle only |
| 2. Resultados       | Per test type: summary table + pass/fail rates                     | Each cycle |
| 3. Defectos         | Defect register ordered by test type (ID, severity, …, evidence)   | Each cycle |
| 4. Evaluación       | Metrics, graphs (pass rate, defects by severity)                   | Final cycle only |
| 5. Recomendaciones  | Suggested fixes and improvements                                   | Each cycle |
| 6. Referencias      | IEEE format                                                        | Final cycle only |
| 7. Anexos           | Project structure, source code excerpts, defect format, evidence   | Each cycle |

> Sections 1, 4 and 6 are produced **only once all US are complete** (they need the global
> picture). Per-US/partial reports include 2, 3, 5 and 7. This is what the current
> `Informe de Pruebas - US01 y US04.docx` does.

**Versionado:** `gen_informe.js` **sí** se versiona (código reproducible). El **`.docx` NO**:
es un entregable de uso personal y `tests/SQA/.gitignore` lo excluye con la regla
`/reports/*.docx`. Cualquiera puede regenerar el informe ejecutando `gen_informe.js`.

---

## Checklist before committing

- [ ] `.env` is **not** staged (it's in `.gitignore`) — verify with `git check-ignore <path>/.env`
- [ ] `.claude/` is **not** staged (it's in `.gitignore`)
- [ ] No `__pycache__/`, `*.pyc` or `.pytest_cache/` staged (covered by root `.gitignore`)
- [ ] No leftover `debug_*.py` scripts or `_debug_*.png` in the US folder
- [ ] All test files collect: `pytest automated/ --collect-only -q`
- [ ] Suite was actually run and the result matches the documented Status in each case `.md`
- [ ] Case markdown files have correct CP-HUxx-NN IDs and filled Actual result / Status / Evidence
- [ ] Any defect has its `evidence/DEF-USxx-NN_*.md` and the test is marked `xfail`
- [ ] `evidence/.gitkeep` and `reports/.gitkeep` are committed (so folders exist in repo)
- [ ] Test data was cleaned from the instance (no residual licenses/users/assets/master data)
- [ ] Settings toggled for tests (e.g. `unique_serial`) were restored to their original value
- [ ] Commit author is María Paula Castillo Chinchilla (PauCCH); **no Co-Authored-By: Claude** trailer

---

## Quick start for the next US (TL;DR)

1. `git checkout master && git checkout -b USxx-TestCases` (or branch from the closest US).
2. Read the US's cases in `Plan de Pruebas.docx`; note tool, technique and type per case.
3. Copy the closest existing US folder; copy its `.env`.
4. Inspect the real form/flow HTML (login + `curl` the page, or a throwaway Playwright script)
   to capture **real selectors** before coding Page Objects.
5. Write fixtures (data setup+teardown via `_api`), Page Objects, then `test_huXX_*.py`.
6. Run the suite, fix selectors, document each case `.md` with real results.
7. Log any defect (DEF-USxx-NN) and mark its test `xfail`.
8. Generate the HTML report; extend `gen_informe.js` if updating the `.docx`.
9. Clean test data, restore toggled settings, run the commit checklist, commit under your name.