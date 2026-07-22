# Payroll Panel

An internal RTL (Persian) web panel for auditing farm payroll ("صورت کارگری") and
fertilizer-consumption ("مصرف کود") Excel workbooks. Operators upload monthly
`.xlsx` workbooks; the app validates and audits them (flagging missing/negative/zero
amounts), writes back a highlighted copy of the workbook, optionally backs the file
up to Google Drive, and persists everything to PostgreSQL. Accountants get a
dashboard, month-by-month drill-down, default reports with charts, a natural-language
chat-style report assistant, an archive of all uploads, and user management.

This is a from-zero rebuild of a legacy single-file FastAPI app (kept for reference
under `legacy/`) into a layered, testable, Dockerized application. See
[`docs/REBUILD_PLAN.md`](docs/REBUILD_PLAN.md) for the original rebuild plan this
implementation follows.

## Tech stack

- **Backend:** Python 3.11+ / [FastAPI](https://fastapi.tiangolo.com/), served by
  Gunicorn with Uvicorn workers.
- **Database:** PostgreSQL, via SQLAlchemy 2.0 (typed models) + Alembic migrations.
- **Auth:** Single scheme — httpOnly, DB-backed cookie sessions (no JWT), passwords
  hashed with `passlib`/`bcrypt`.
- **Audit engine:** `openpyxl`-based workbook parsing/highlighting, vendored in
  `audit_engine/` (see `audit_engine/README.md` for provenance).
- **Cloud backup:** Google Drive, via `google-api-python-client` + a service account
  (`app/services/drive_service.py`), fully optional/config-driven.
- **Frontend:** [Vite](https://vite.dev/) + React 19 + TypeScript SPA, RTL/Persian
  UI, [react-router-dom](https://reactrouter.com/) for routing, and
  [Chart.js](https://www.chartjs.org/) (`react-chartjs-2`) for report charts.
- **Deployment:** Docker + docker-compose (`web` / `db` / `nginx` / one-shot
  `frontend-build`).
- **Testing/CI:** `pytest` (backend, SQLite in-memory), `oxlint` + `tsc` (frontend),
  `ruff` (backend lint), GitHub Actions (`.github/workflows/ci.yml`).

## Project structure

```
payroll-panel/
  app/
    main.py              # FastAPI app factory — registers all routers, CORS, healthz
    config.py             # pydantic-settings, env-driven configuration
    db.py                 # SQLAlchemy engine/session, get_db dependency
    seed.py                # Seeds default operator/accountant users (python -m app.seed)
    models/               # SQLAlchemy models: User, Session, Upload, AuditIssue, ChatMessage
    schemas/              # Pydantic request/response models (auth, upload, chat)
    api/
      auth.py             # login / logout / me + user CRUD (accountant-only)
      uploads.py          # payroll xlsx upload -> audit -> Drive backup -> DB
      fertilizer.py       # fertilizer xlsx upload -> audit -> Drive backup -> DB
      reports.py          # months / month detail / archive / default reports (DB-backed)
      chat.py              # chat-style report assistant + history (accountant-only)
    services/
      auth_service.py     # authenticate/login/logout, user CRUD business logic
      audit_service.py    # thin wrapper around audit_engine (payroll + fertilizer)
      upload_service.py   # upload orchestration: validate, hash, audit, highlight, persist
      storage_service.py  # local filesystem storage for uploaded/highlighted workbooks
      drive_service.py    # Google Drive backup (service account, config-driven)
      chat_service.py     # NL routing over ingested payroll data + chart HTML generation
    core/
      security.py         # password hashing, session helpers, RBAC dependency guards
  audit_engine/            # Vendored, from-scratch reimplementation of the original
                           # ~/.hermes payroll/fertilizer audit scripts (see its README)
  migrations/              # Alembic migrations (baseline schema + chat_messages)
  frontend/                # Vite + React + TypeScript SPA (see frontend/ section below)
  tests/                   # pytest suite: auth, RBAC, uploads, audit_engine
  deploy/
    nginx.conf             # Reverse proxy: /api/ -> web, / -> built SPA (with SPA fallback)
    certs/                 # TLS certs mounted into nginx (see Deployment notes)
    REBUILD_PLAN.md        # Copy of the original rebuild plan
  legacy/                  # Original monolithic app.py + static HTML, kept for reference only
  docs/
    REBUILD_PLAN.md        # The rebuild plan this implementation follows
  data/, uploads/          # Local dev data / uploaded workbook storage (gitignored)
  Dockerfile               # Backend image (installs app + audit_engine, runs gunicorn)
  docker-compose.yml       # db + web + nginx + frontend-build services
  alembic.ini
  pyproject.toml           # Backend package metadata + dependencies (incl. dev extras)
  .env.example             # Template for required environment variables
```

## Data model

Replaces the legacy JSON files (`users.json`, `sessions.json`, `index.json`,
`fertilizer_index.json`, `chat_history.json`) with real tables:

- **`users`** — id, username, password_hash, role (`operator`/`accountant`), name,
  is_active, created_at.
- **`sessions`** — token (PK), user_id, created_at, expires_at. Backing the single
  httpOnly-cookie auth scheme.
- **`uploads`** — one row per ingested workbook (payroll or fertilizer), keyed by
  `(upload_type, month_key)`. Stores original filename, sha256, local paths to the
  stored + highlighted workbook, Drive backup id/error, error/warn counts, and a
  JSON `audit_summary` blob (per-sheet stats for payroll; row/fertilizer counts for
  fertilizer).
- **`audit_issues`** — one row per audit finding (severity/code/sheet/message),
  linked to an upload.
- **`chat_messages`** — user/assistant turns for the report-assistant chat, with
  optional rendered chart HTML.

## Prerequisites

- Python 3.11+
- Node.js 20+ (for the frontend)
- PostgreSQL 16 (or use the bundled `docker-compose` `db` service)
- Docker + Docker Compose, if you want to run the whole stack in containers

## Environment variables

Copy `.env.example` to `.env` and fill in real values — **never commit `.env`**:

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development` or `production`; controls secure cookie flag |
| `APP_HOST` / `APP_PORT` | Bind address for uvicorn/gunicorn (default `0.0.0.0:8765`) |
| `APP_SECRET_KEY` | Required, min 32 chars; no insecure placeholder accepted |
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg://payroll:payroll@db:5432/payroll_panel` |
| `SESSION_COOKIE_NAME` | httpOnly session cookie name (default `payroll_session`) |
| `SESSION_TTL_HOURS` | Session lifetime (default `168` = 7 days) |
| `UPLOAD_DIR` | Where uploaded/highlighted workbooks are stored |
| `DATA_DIR` | General app data directory |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to a Google service-account JSON for Drive backup (optional — uploads still work without it, just skip the Drive backup and record a `drive_error`) |
| `DRIVE_PARENT_FOLDER_ID` | Optional; if unset, the app looks up/creates a folder named `DRIVE_FOLDER_NAME` |
| `DRIVE_FOLDER_NAME` | Drive folder name to use/create when `DRIVE_PARENT_FOLDER_ID` is unset |
| `CORS_ORIGINS` | Comma-separated allowed origins; blank = same-origin only |

Additionally, `app/seed.py` reads these (not in `.env.example`, set them when you
want the seed script to actually create users):

| Variable | Purpose |
|---|---|
| `SEED_OPERATOR_USERNAME` / `SEED_OPERATOR_PASSWORD` / `SEED_OPERATOR_NAME` | Default operator account (username defaults to `operator1`) |
| `SEED_ACCOUNTANT_USERNAME` / `SEED_ACCOUNTANT_PASSWORD` / `SEED_ACCOUNTANT_NAME` | Default accountant account (username defaults to `admin1`) |

The seed script is idempotent — it skips users that already exist, and skips
creating a user entirely if its password env var isn't set.

## Running with Docker Compose (recommended)

This brings up Postgres, the FastAPI backend, and nginx serving the built SPA:

```bash
cp .env.example .env
# edit .env — at minimum set a real APP_SECRET_KEY

# Build the frontend once (writes into the shared frontend_dist volume)
docker compose run --rm frontend-build

# Start the rest of the stack
docker compose up -d db web nginx
```

- `web` runs `alembic upgrade head`, then `python -m app.seed`, then starts
  gunicorn — so migrations and seeding happen automatically on every start.
- `nginx` listens on `:80`/`:443`, proxies `/api/` to `web:8765`, and serves the
  built SPA (with `try_files` SPA fallback) from `deploy/nginx.conf`.
- Re-run `docker compose run --rm frontend-build` whenever you change the
  frontend, then restart `nginx` if needed.
- Google Drive backup: place your service-account JSON under `./secrets/` (the
  default `GOOGLE_CREDENTIALS_PATH`) so it's mounted read-only at `/secrets` in the
  `web` container, matching `GOOGLE_APPLICATION_CREDENTIALS=/secrets/google-service-account.json`.

## Running locally without Docker

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# passlib's bcrypt backend currently requires bcrypt <4.1
pip install "bcrypt>=4.0,<4.1"

cp .env.example .env   # edit APP_SECRET_KEY and DATABASE_URL for local Postgres

# Run migrations
alembic upgrade head

# Seed default users (set SEED_*_PASSWORD env vars first, see above)
python -m app.seed

# Start the API with autoreload
uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

The API is now at `http://localhost:8765`, with a health check at
`GET /api/healthz`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

`vite.config.ts` proxies `/api` requests to `http://localhost:8765`, so run the
backend first. The dev server prints its own URL (default `http://localhost:5173`).

Other frontend scripts:

```bash
npm run lint     # oxlint
npm run build    # tsc -b && vite build -> frontend/dist
npm run preview  # preview the production build locally
```

## Running tests

### Backend (pytest)

```bash
source .venv/bin/activate
pytest -q
```

Tests use an isolated in-memory SQLite database per test (see `tests/conftest.py`)
and a FastAPI `TestClient` with `get_db` overridden — no real Postgres or Docker
required. Coverage includes:

- `tests/test_auth.py` — login/logout, `/api/me`, invalid credentials, session
  invalidation.
- `tests/test_rbac.py` — operator vs accountant access to protected endpoints
  (`/api/users`, `/api/reports/data`, `/api/months`, user CRUD).
- `tests/test_uploads.py` — xlsx validation, auth requirement, successful
  upload + persistence, duplicate-month detection with/without `replace`, invalid
  month key format.
- `tests/test_audit_engine.py` — payroll/fertilizer workbook auditing: happy path,
  negative-amount/quantity detection, missing-header detection, highlighted-workbook
  writing, Persian-digit number parsing.

### Lint

```bash
ruff check app audit_engine tests
```

### CI

`.github/workflows/ci.yml` runs on every push/PR to `main`:

- **backend** job: installs the package with dev extras, runs `ruff check`, then
  `pytest -q` against an in-memory SQLite DB.
- **frontend** job: `npm ci`, `npm run lint` (oxlint), and `npm run build`
  (type-checks with `tsc -b` and builds with Vite).

## Deployment notes

- **TLS:** `deploy/nginx.conf` listens on plain `:80` by default and proxies to
  `web`; a commented-out `listen 443 ssl` server block (plus an HTTP->HTTPS
  redirect) is included and ready to enable. `docker-compose.yml` exposes `:443`
  and mounts `deploy/certs/` read-only into the nginx container. To enable HTTPS:
  1. Add `fullchain.pem` + `privkey.pem` under `deploy/certs/` — either from a real
     CA (see `deploy/certs/README.md` for a Let's Encrypt example) or, for local
     testing, run `deploy/certs/generate-self-signed.sh`.
  2. Uncomment the `listen 443 ssl` block and the `:80` -> `:443` redirect in
     `deploy/nginx.conf`.
  3. `docker compose up -d nginx` to reload with the new config.
- **Secrets:** never commit `.env` or the Google service-account JSON. In
  production, set `APP_ENV=production` so session cookies get the `secure` flag.
- **Database migrations:** the `web` service runs `alembic upgrade head` on every
  container start, so deploying a new revision is just `docker compose up -d web`
  (or restart) after pulling the new image/migration files.
- **Seeding:** `python -m app.seed` is safe to re-run — it only creates the
  operator/accountant accounts if they don't already exist and their password env
  vars are set; otherwise it's a no-op.
- **Frontend rebuilds:** the SPA is a separate build step
  (`docker compose run --rm frontend-build`) that writes into the shared
  `frontend_dist` volume nginx serves from — rebuild and restart `nginx` after
  frontend changes.
- **File storage:** uploaded and highlighted workbooks live under `UPLOAD_DIR`
  (mounted as the `uploads_data` volume in compose); back this up independently of
  the database if you rely on local storage rather than (or in addition to) Google
  Drive backup.
