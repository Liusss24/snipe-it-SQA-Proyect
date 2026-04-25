# Smoke Checklist

Use this checklist after setup or major changes.

## Environment

- [ ] `.env.testing` exists and points to test DB
- [ ] `php artisan key:generate --env=testing` has been run (if needed)
- [ ] `php artisan migrate --env=testing` runs without errors

## Core application

- [ ] Login page loads
- [ ] User can authenticate with valid credentials
- [ ] Dashboard loads after login
- [ ] Main navigation renders correctly

## Core modules

- [ ] Assets list loads
- [ ] Users list loads
- [ ] Locations list loads
- [ ] Categories list loads

## API and security basics

- [ ] API health/basic endpoint responds (if applicable)
- [ ] Unauthorized access is rejected on protected pages
- [ ] CSRF protected form submits correctly

## Automated baseline

- [ ] `php artisan test --testsuite=Unit` passed
- [ ] `php artisan test --testsuite=Feature` passed
