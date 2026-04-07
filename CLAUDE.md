# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

HireTrail — a job search tracker with a FastAPI backend and Streamlit frontend.

## Commands

All commands must be run with the virtual environment activated, or prefixed with `venv/bin/`.

```bash
# Activate venv (do this first)
source venv/bin/activate

# Start Postgres (first time or after machine restart)
docker compose up -d

# Run the API server (hot-reload enabled)
uvicorn app.main:app --reload --port 8000

# Run the Streamlit UI
streamlit run streamlit_app.py --server.port 8501

# Run all tests
pytest

# Run tests verbose
pytest -v

# Run a single test file
pytest app/tests/test_companies.py -v

# Run a specific test
pytest app/tests/test_applications.py::test_create_application -v

# Install dependencies
pip install -r requirements.txt

# Alembic — apply migrations
alembic upgrade head

# Alembic — generate a new migration after changing models.py
alembic revision --autogenerate -m "describe your change"

# Migrate existing SQLite data to Postgres (one-time)
python scripts/migrate_sqlite_to_postgres.py
```

The `.claude/launch.json` has pre-configured server entries for `preview_start`:
- `"HireTrail API"` → uvicorn on port 8000
- `"HireTrail UI"` → streamlit on port 8501

## Database

The app reads `DATABASE_URL` from `.env` (loaded via `python-dotenv`). Falls back to `sqlite:///./hiretrail.db` if the variable is not set.

```
# .env
DATABASE_URL=postgresql://hiretrail:hiretrail@localhost:5432/hiretrail
```

Local Postgres is managed via `docker-compose.yml` — a single `postgres:16` container with a named volume for persistence. Schema is managed by Alembic (`alembic upgrade head`). `Base.metadata.create_all()` still runs at startup as a safety net for first-run, but Alembic is the source of truth for schema changes.

Tests always use a separate in-process `sqlite:///./test.db`, injected via `app.dependency_overrides[get_db]`, so they never touch Postgres.

## Architecture

### Backend (`app/`)

The API layer follows a strict 4-layer separation:

```
Request → Router → CRUD → Model (SQLAlchemy) → Postgres (or SQLite fallback)
                ↕
            Schema (Pydantic)
```

- **`models.py`** — SQLAlchemy ORM table definitions. The three core entities are `Company`, `Application`, and `Interview`, with `Company → Application → Interview` as the relationship chain. `company_id` on `Application` is nullable (company is optional).
- **`schemas.py`** — Pydantic models for request validation and response serialization. Each entity has `Base`, `Create`, `Update`, and `Out` variants. Business rules (salary range, non-empty strings) are enforced here via validators.
- **`crud.py`** — All database read/write operations. No business logic lives here.
- **`routers/`** — One file per entity (`companies.py`, `applications.py`, `interviews.py`, `imports.py`). Routers only call CRUD functions and raise `HTTPException`.
- **`database.py`** — Reads `DATABASE_URL` from env, builds the engine, and exposes `get_db()` as a FastAPI dependency.

### Key design decisions

- `ApplicationStatus` and `InterviewResult` are Python `str` enums defined in `models.py` and imported into `schemas.py`.
- Schema migrations are managed by **Alembic** (`alembic/`). After changing `models.py`, run `alembic revision --autogenerate -m "..."` then `alembic upgrade head`. `Base.metadata.create_all()` still runs at startup as a first-run convenience.
- Tests use a separate `test.db` (SQLite), injected via `app.dependency_overrides[get_db]`. Each test function gets a fresh schema via the `setup_db` autouse fixture.

### CSV Import (`routers/imports.py`)

`POST /import/applications` accepts a CSV file upload. It auto-detects column names via `COLUMN_ALIASES` (case-insensitive fuzzy matching), normalizes status strings via `STATUS_MAP`, and auto-creates `Company` records for new company names using `db.flush()` to batch inserts before commit.

### Frontend (`streamlit_app.py`)

Single-file Streamlit app. Navigation order: Applications → Interviews → Companies. All API calls go through four thin helpers: `api_get`, `api_post`, `api_put`, `api_delete`. `API_BASE` is resolved from `st.secrets["API_BASE"]`, then `$API_BASE` env var, then falls back to `http://localhost:8000`. Both servers must be running simultaneously for the UI to work. All list fetches use `limit=10000` to avoid the API's default cap of 100.

## Enums reference

**ApplicationStatus:** `wishlist` | `applied` | `interviewing` | `offer` | `rejected` | `withdrawn`

**InterviewResult:** `pending` | `passed` | `failed`
