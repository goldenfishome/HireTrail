"""
Migrate data from SQLite (hiretrail.db) to Postgres.

Prerequisites:
  1. Postgres is running and DATABASE_URL is set in .env
  2. Tables already exist in Postgres (run: alembic upgrade head)

Usage:
  python scripts/migrate_sqlite_to_postgres.py
"""
import os
import sqlite3
import sys
from urllib.parse import urlparse

import psycopg2
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = "hiretrail.db"
PG_URL = os.getenv("DATABASE_URL")


def connect_postgres():
    p = urlparse(PG_URL)
    return psycopg2.connect(
        host=p.hostname,
        port=p.port or 5432,
        user=p.username,
        password=p.password,
        dbname=p.path.lstrip("/"),
    )


def migrate():
    if not os.path.exists(SQLITE_PATH):
        print(f"ERROR: {SQLITE_PATH} not found. Run from the project root.")
        sys.exit(1)

    if not PG_URL:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)

    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row
    cur = sqlite.cursor()

    pg = connect_postgres()
    pgc = pg.cursor()

    # ── Companies ──────────────────────────────────────────────────────────────
    cur.execute("SELECT * FROM companies")
    companies = cur.fetchall()
    for c in companies:
        pgc.execute(
            """
            INSERT INTO companies (id, name, website, location, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (c["id"], c["name"], c["website"], c["location"], c["notes"], c["created_at"]),
        )
    print(f"  companies  : {len(companies)} rows")

    # ── Applications ───────────────────────────────────────────────────────────
    cur.execute("SELECT * FROM applications")
    applications = cur.fetchall()
    for a in applications:
        pgc.execute(
            """
            INSERT INTO applications
              (id, company_id, role_title, status, job_link,
               date_applied, source, salary_min, salary_max,
               notes, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                a["id"], a["company_id"], a["role_title"], a["status"],
                a["job_link"], a["date_applied"], a["source"],
                a["salary_min"], a["salary_max"],
                a["notes"], a["created_at"], a["updated_at"],
            ),
        )
    print(f"  applications: {len(applications)} rows")

    # ── Interviews ─────────────────────────────────────────────────────────────
    cur.execute("SELECT * FROM interviews")
    interviews = cur.fetchall()
    for i in interviews:
        pgc.execute(
            """
            INSERT INTO interviews
              (id, application_id, round_name, interview_date,
               interviewer_name, result, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                i["id"], i["application_id"], i["round_name"],
                i["interview_date"], i["interviewer_name"],
                i["result"], i["notes"], i["created_at"],
            ),
        )
    print(f"  interviews  : {len(interviews)} rows")

    # ── Reset Postgres sequences so future inserts get the right IDs ───────────
    for table in ["companies", "applications", "interviews"]:
        pgc.execute(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}"
        )

    pg.commit()
    pgc.close()
    pg.close()
    sqlite.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    print("Migrating data from SQLite → Postgres...")
    migrate()
