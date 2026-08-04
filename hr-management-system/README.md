# HR Management System

A production-style HR platform built with Flask, SQLAlchemy 2.0, PostgreSQL, and Redis.

## Features

- **Employee management** — profiles, department hierarchy, manager chains
- **Attendance** — self-service check-in/out, HR corrections, history
- **Leave management** — apply, approve/reject workflow, per-type balances, email notifications
- **Payroll** — salary structures, async monthly payroll generation, PDF payslips
- **Documents** — per-employee uploads (contracts, IDs, certificates)
- **Role-based access control** — Admin / HR / Employee, enforced via decorators
- **Reports** — PDF attendance and leave summary exports
- **Audit logs** — every mutating action recorded
- **Background jobs** — Redis + RQ worker for emails and payroll generation

## Tech Stack

Python · Flask · SQLAlchemy 2.0 (tables auto-created, no migrations) · Jinja2 · PostgreSQL · Redis · RQ · Docker · Pytest

## Project Structure

```
app/
  models/           # SQLAlchemy 2.0 models (typed Mapped[] style)
  blueprints/       # One package per feature area (auth, employees, leave, payroll, ...)
  templates/        # Jinja2 templates, mirrors blueprint structure
  static/           # CSS + uploaded files
  utils/            # PDF generation, email dispatch, background tasks, audit logging
  decorators.py     # @roles_required / @self_or_roles_required RBAC decorators
  config.py         # Dev / Testing / Production config classes
  extensions.py     # Flask extension singletons (avoids circular imports)
  cli.py            # `flask create-admin`, `flask seed-db`
tests/              # Pytest suite (auth, RBAC boundaries, leave workflow)
docker/             # Dockerfile
docker-compose.yml  # web + worker + postgres + redis
worker.py           # RQ worker entrypoint
wsgi.py             # App entrypoint for gunicorn
```

## Quickstart (Docker)

```bash
cp .env.example .env        # edit values as needed
docker compose up --build
docker compose exec web flask seed-db         # seed leave types + default department
```

Tables are created automatically on first startup — no migration step needed.
A default admin account is also seeded automatically:

- **Username:** `hamid`
- **Password:** `hamid123`

Visit http://localhost:5000 — you'll land on the public homepage. Click **Log In**
and use the admin credentials above, or click **Sign Up** to create a regular
employee account.

## Quickstart (local, without Docker)

Requires a local PostgreSQL and Redis instance.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # point DATABASE_URL / REDIS_URL at your local services

flask seed-db                # seeds leave types + default department
                              # (tables + the default admin user "hamid"/"hamid123"
                              #  are created automatically on first run)

flask run                    # web app
python worker.py             # in a second terminal — background job worker
```

## Running Tests

Tests use an isolated, per-test SQLite database — no external services required:

```bash
pip install -r requirements.txt
pytest -v
```

## Notes on Design Decisions

- **`User` vs `Employee`** are separate models. Every `Employee` has exactly one `User` (login identity + role), but this keeps room for pure-system accounts that aren't on the payroll.
- **RBAC** is enforced at the route layer via `@roles_required(...)` and `@self_or_roles_required(...)` decorators — the latter lets an employee see their own records (e.g. payslips) while still gating HR/Admin-wide access.
- **Background jobs** (payroll generation, emails) are dispatched to Redis/RQ so slow work never blocks a web request. Each falls back to a synchronous call if Redis is unreachable, so the app still works in a minimal dev setup without the worker running.
- **Audit log** entries are added to the session but not committed independently — they ride along in the same transaction as the action they're logging, so you never get an audit entry for a write that didn't actually happen.

## What's Scaffolded vs. What You'll Want to Extend

This is a complete, working skeleton with one fully fleshed-out reference module (`employees`) and working — but intentionally lean — implementations of the rest. Natural next steps:
- Flesh out template styling / add a proper design system
- Add pagination to more list views (attendance, leave, payroll)
- Expand test coverage (payroll generation, document upload, department hierarchy)
- Add email templates styling, and a "forgot password" flow
- Add per-department leave-approval routing (currently HR/Admin approve everything)
