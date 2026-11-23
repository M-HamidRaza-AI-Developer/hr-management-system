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

## Default Admin

On first startup a default admin account is created automatically:

- **Username:** `hamid`
- **Password:** `hamid123`

Change this password before any real deployment. You can also click **Sign Up**
to create a regular employee account.

## Quickstart (Docker)

```bash
cp .env.example .env        # edit values as needed
docker compose up --build
docker compose exec web flask seed-db         # seed leave types + default department
```

Tables are created automatically on first startup — no migration step needed.
Visit http://localhost:5000 and click **Log In**.

## Quickstart (local, without Docker)

Requires a local PostgreSQL instance. Redis is optional (see notes below).

### 1. Environment

Linux / macOS:
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Create the PostgreSQL database

Open `psql` (SQL Shell) as the `postgres` user and run:

```sql
CREATE USER hr_user WITH PASSWORD 'hr_password';
CREATE DATABASE hr_management OWNER hr_user;
\c hr_management
GRANT ALL ON SCHEMA public TO hr_user;
```

### 3. Configure `.env`

Copy `.env.example` to `.env`. When running **outside Docker**, the hosts must be
`localhost` (the names `db` and `redis` only exist inside the Docker network):

```
DATABASE_URL=postgresql://hr_user:hr_password@localhost:5432/hr_management
REDIS_URL=redis://localhost:6379/0
```

### 4. Seed and run

```bash
flask seed-db      # seeds leave types + default department (safe to re-run)
flask run          # web app at http://127.0.0.1:5000
python worker.py   # optional, in a second terminal: background job worker
```

Log in with the default admin (`hamid` / `hamid123`).

**Redis on Windows:** Redis does not run natively on Windows. The app still works
without it, because emails and payroll fall back to synchronous execution when Redis
is unreachable. Use Docker, WSL, or Memurai if you want the background worker.

## Troubleshooting

| Error / symptom | Cause and fix |
|---|---|
| `could not translate host name "db"` | `.env` uses the Docker hostname. Change `db` to `localhost` in `DATABASE_URL`. |
| `connection to server at "localhost" failed: Connection refused` | PostgreSQL is not running. Start the