# SQA Test Workspace

This folder centralizes SQA assets for this project.

## Structure

- `checklists/`: smoke and regression checklists.
- `cases/`: reusable manual test case templates.
- `evidence/`: screenshots, logs, and supporting files.
- `reports/`: execution summaries and defect reports.

## Suggested flow

1. Configure test environment:
   - Copy `.env.testing.example` to `.env.testing`
   - Set DB values for your test database
2. Run baseline automated tests:
   - `php artisan test --testsuite=Unit`
   - `php artisan test --testsuite=Feature`
3. Execute manual smoke checklist.
4. Execute regression checklist by module.
5. Save evidence in `evidence/` and final report in `reports/`.

## Naming convention

Use this pattern for files in `evidence/` and `reports/`:

`YYYY-MM-DD_module_testType_description`

Example:

`2026-04-25_assets_smoke_create-asset.png`
