# SQA Project Structure — Initialization Guide

This document explains the conventions, folder layout, and initialization steps for
any new User Story (US) test branch in this project. Use it as the entry point when
starting QA work on a new US.

---

## Context

- **Project:** Snipe-IT (fork – SQA analysis)
- **Repository:** `snipe-it-SQA-Proyect`
- **Main branch:** `master`
- **Pattern per US:** one dedicated Git branch named `USxx-TestCases`
- **Test Plan document:** `C:\Users\Aaron\Downloads\Plan de Pruebas.docx`
- **Report template:** `C:\Users\Aaron\Downloads\Informe de Pruebas.docx`

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
│   ├── cases/
│   │   └── manual-test-case-template.md
│   ├── checklists/
│   ├── evidence/
│   ├── reports/
│   │
│   └── USxx-TestCases/           ← NEW folder for each US
│       ├── README.md             ← index of test cases, setup, run instructions
│       ├── requirements.txt      ← Python deps (pytest, playwright, etc.)
│       ├── pytest.ini            ← pytest config (markers, output, screenshot)
│       ├── .env.example          ← environment variables template (NEVER commit .env)
│       ├── conftest.py           ← shared fixtures: browser, auth, test data
│       │
│       ├── pages/                ← Page Object Models (one file per UI page)
│       │   ├── __init__.py
│       │   ├── login_page.py
│       │   └── <module>_page.py
│       │
│       ├── automated/            ← pytest test files
│       │   ├── __init__.py
│       │   └── test_huXX_NN_MM_<description>.py
│       │
│       ├── cases/                ← Documented test cases (Markdown, one per CP)
│       │   ├── CP-HUxx-01.md
│       │   └── ...
│       │
│       ├── evidence/             ← Screenshots and logs per execution run
│       │   └── .gitkeep
│       │
│       └── reports/              ← HTML/text execution reports
│           └── .gitkeep
│
└── Feature/                      ← Laravel/PHPUnit tests (existing, do not modify)
```

---

## Tools per test type

| Test type        | Tools                                   | Notes                              |
|------------------|-----------------------------------------|------------------------------------|
| UI / Sistema     | Python 3.12 + pytest + Playwright       | Chromium, 1920×1080                |
| UI / Integración | Python 3.12 + pytest + Playwright       | Cross-module checks                |
| Manual           | Markdown case file + manual execution   | Fill "Actual result" and evidence  |
| Performance      | JMeter                                  | Separate `.jmx` project            |
| Unit / Backend   | Pest (PHP)                              | `php artisan test --testsuite=...` |

---

## Environment setup for a new US

```bash
# 1. Create the US folder (copy from US04 as template)
cp -r tests/SQA/US04-TestCases tests/SQA/USxx-TestCases

# 2. Update README.md, cases/, and automated/ with new test IDs and logic

# 3. Copy and fill in the .env
cp tests/SQA/USxx-TestCases/.env.example tests/SQA/USxx-TestCases/.env

# 4. Install Python deps
cd tests/SQA/USxx-TestCases
pip install -r requirements.txt
playwright install chromium

# 5. Verify Snipe-IT is running and the API token is valid
```

---

## conftest.py conventions

| Variable                    | Source        | Purpose                                   |
|-----------------------------|---------------|-------------------------------------------|
| `SNIPEIT_BASE_URL`          | `.env`        | Base URL, no trailing slash               |
| `SNIPEIT_ADMIN_USERNAME`    | `.env`        | Admin login for `auth_page` fixture       |
| `SNIPEIT_ADMIN_PASSWORD`    | `.env`        | Admin password                            |
| `SNIPEIT_API_TOKEN`         | `.env`        | Bearer token for test-data setup via API  |
| `SNIPEIT_NOPERM_USERNAME`   | `.env`        | User with restricted permissions          |

Key fixtures to reuse or adapt:

- `page` — plain browser page
- `auth_page` — page already logged in as admin
- `noperm_page` — page logged in as restricted user
- `base_url` — session-scoped base URL string

Test-data fixtures must **create and clean up** resources (yield + DELETE via API).

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

## Report (Informe de Pruebas)

After test execution, populate the report following the template at
`C:\Users\Aaron\Downloads\Informe de Pruebas.docx`:

| Section             | Content                                                            |
|---------------------|--------------------------------------------------------------------|
| 1. Introducción     | Scope, objective, methodology, limitations                         |
| 2. Resultados       | Per test type: summary table + pass/fail rates                     |
| 3. Defectos         | Defect register (ID, severity, description, evidence)              |
| 4. Evaluación       | Metrics, graphs (pass rate, defects by severity)                   |
| 5. Recomendaciones  | Suggested fixes and improvements                                   |
| 6. Referencias      | IEEE format                                                        |
| 7. Anexos           | Test case markdowns, evidence screenshots, source + test code      |

Paste the test case markdown files (from `cases/`) directly into the Annexes section.

---

## Checklist before committing

- [ ] `.env` is **not** staged (it's in `.gitignore`)
- [ ] `.claude/` is **not** staged (it's in `.gitignore`)
- [ ] All new Python files pass `python -m py_compile <file>` (no syntax errors)
- [ ] Case markdown files have the correct CP-HUxx-NN IDs
- [ ] `evidence/.gitkeep` and `reports/.gitkeep` are committed (so folders exist in repo)
- [ ] Commit author is Aarón Líos Cubillo (Liusss24)
