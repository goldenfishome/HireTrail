# HireTrail

A job search tracker with a FastAPI backend and Streamlit frontend. Track companies, job applications, and interview rounds — with CSV import, status filtering, and a live dashboard.

**Live demo:**
- 🖥️ [Dashboard](https://goldenfishome-hiretrail-streamlit-app-58tcdl.streamlit.app/) — Streamlit UI
- 📡 [API docs](https://hiretrail-api-d8z8.onrender.com/docs) — Interactive FastAPI documentation

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI + Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL (SQLite fallback for tests) |
| Migrations | Alembic |
| Frontend | Streamlit |
| Server | Uvicorn |

## Features

- Full CRUD for **Companies**, **Applications**, and **Interviews**
- Application tracking with statuses: `wishlist` → `applied` → `interviewing` → `offer` / `rejected` / `withdrawn`
- Interview round tracking with results: `pending` / `passed` / `failed`
- **CSV import** — upload a spreadsheet export and auto-detect columns (`title`, `company`, `date`, `link`, `status`, etc.)
- Filter applications by status, company, and sort field
- Streamlit dashboard with metrics (total, interviewing, offers, rejected)

## Architecture

```
Client (Streamlit UI)
        │
        ▼
   FastAPI (port 8000)
        │
   Pydantic schemas  ◄── validation & serialization
        │
   SQLAlchemy CRUD
        │
   PostgreSQL
```

The backend follows a strict 4-layer separation: **Router → CRUD → Model → Database**. Routers only call CRUD functions and raise `HTTPException`. Business rules (salary range, non-empty strings) live in Pydantic schemas.

## Local setup

**Prerequisites:** Python 3.11+, Docker

```bash
# 1. Clone and create virtual environment
git clone https://github.com/goldenfishome/hiretrail
cd hiretrail
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start Postgres
docker compose up -d

# 3. Set environment variable
cp .env.example .env   # already filled in for local Docker setup

# 4. Run database migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload --port 8000

# 6. Start the UI (new terminal)
streamlit run streamlit_app.py --server.port 8501
```

Open **http://localhost:8501** for the UI, **http://localhost:8000/docs** for the interactive API docs.

## API endpoints

### Companies
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/companies/` | Create a company |
| `GET` | `/companies/` | List all companies |
| `GET` | `/companies/{id}` | Get a company |
| `PUT` | `/companies/{id}` | Update a company |
| `DELETE` | `/companies/{id}` | Delete a company |

### Applications
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/applications/` | Create an application |
| `GET` | `/applications/` | List applications (filter by `status`, `company_id`, `sort_by`) |
| `GET` | `/applications/{id}` | Get an application |
| `PUT` | `/applications/{id}` | Update an application |
| `DELETE` | `/applications/{id}` | Delete an application |
| `POST` | `/import/applications` | Bulk import from CSV |

### Interviews
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/interviews/` | Log an interview round |
| `GET` | `/interviews/` | List interviews (filter by `application_id`) |
| `GET` | `/interviews/{id}` | Get an interview |
| `PUT` | `/interviews/{id}` | Update an interview |
| `DELETE` | `/interviews/{id}` | Delete an interview |

## CSV import

`POST /import/applications` accepts a `.csv` file and auto-detects columns by name (case-insensitive). Supported column names:

| Field | Accepted column names |
|---|---|
| Job title | `title`, `job_title`, `role`, `position` |
| Company | `company`, `employer` |
| Date applied | `date`, `date_applied`, `applied_date` |
| Job link | `link`, `url`, `job_link`, `posting_url` |
| Status | `status`, `stage` |
| Source | `source`, `platform`, `via` |
| Notes | `notes`, `comments` |

Companies are created automatically if they don't already exist. Status values are normalised (`"Interview"` → `"interviewing"`, `"Rejected"` → `"rejected"`, etc.).

## Running tests

Tests use an isolated in-memory SQLite database and never touch Postgres.

```bash
pytest           # all tests
pytest -v        # verbose
pytest app/tests/test_applications.py::test_create_application -v  # single test
```

## Database migrations

This project uses Alembic for schema migrations. After changing any model in `app/models.py`:

```bash
# Generate a new migration
alembic revision --autogenerate -m "describe your change"

# Apply it
alembic upgrade head
```

## Future improvements

- Authentication (API key or JWT)
- Contacts / recruiters table
- Follow-up reminders
- GitHub Actions CI/CD (run tests on push, auto-deploy on merge to main)
- Export to CSV
