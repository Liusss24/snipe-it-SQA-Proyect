# Regression Checklist

Run this checklist before release or after significant code changes.

## Authentication and authorization

- [ ] Login, logout, password reset
- [ ] Role and permission restrictions validated
- [ ] Access denied views/messages validated

## CRUD and business flows

- [ ] Create, read, update, delete for key entities
- [ ] Validation errors displayed correctly
- [ ] Filters, search, sorting, pagination behave correctly

## Integrations and notifications

- [ ] Email notifications are triggered where expected
- [ ] Import/export flows validated (if enabled)
- [ ] External integrations degrade gracefully on failure

## Stability and data consistency

- [ ] No data corruption after concurrent operations
- [ ] No unexpected duplicate records
- [ ] Audit/action logs generated when expected

## Non-functional checks

- [ ] Basic performance sanity check for heavy pages
- [ ] Accessibility quick pass for critical pages
- [ ] Browser compatibility sanity check (target browsers)

## Defect handling

- [ ] Defects documented with steps to reproduce
- [ ] Severity and priority assigned
- [ ] Re-test status captured after fixes
