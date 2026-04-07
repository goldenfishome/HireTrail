import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/import", tags=["import"])

# ---------------------------------------------------------------------------
# Column aliases — maps our field names to common CSV header variations
# ---------------------------------------------------------------------------
COLUMN_ALIASES = {
    "date_applied":  ["date", "date_applied", "applied_date", "application_date", "applied"],
    "company":       ["company", "company_name", "employer", "organization"],
    "role_title":    ["title", "job_title", "role", "role_title", "position", "job"],
    "job_link":      ["link", "url", "job_link", "job_url", "posting", "posting_url", "application_url"],
    "status":        ["status", "application_status", "stage"],
    "source":        ["source", "applied_via", "platform", "channel", "via"],
    "notes":         ["notes", "note", "comments", "comment", "remarks"],
    "salary_min":    ["salary_min", "min_salary", "salary_from", "pay_min"],
    "salary_max":    ["salary_max", "max_salary", "salary_to",   "pay_max"],
}

# Maps raw CSV status values → valid ApplicationStatus enum values
STATUS_MAP = {
    "applied":       "applied",
    "apply":         "applied",
    "submitted":     "applied",
    "interviewing":  "interviewing",
    "interview":     "interviewing",
    "interviews":    "interviewing",
    "phone screen":  "interviewing",
    "phone":         "interviewing",
    "technical":     "interviewing",
    "offer":         "offer",
    "offered":       "offer",
    "rejected":      "rejected",
    "reject":        "rejected",
    "declined":      "rejected",
    "no offer":      "rejected",
    "not selected":  "rejected",
    "withdrawn":     "withdrawn",
    "withdraw":      "withdrawn",
    "withdrew":      "withdrawn",
    "cancelled":     "withdrawn",
    "wishlist":      "wishlist",
    "saved":         "wishlist",
    "interested":    "wishlist",
    "considering":   "wishlist",
}

DATE_FORMATS = [
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
    "%m-%d-%Y", "%Y/%m/%d", "%d-%m-%Y",
    "%b %d, %Y", "%B %d, %Y", "%d %b %Y",
]


def detect_columns(headers: list) -> dict:
    """Map CSV headers to internal field names, case-insensitively."""
    normalized = {h.strip().lower(): h for h in headers}
    mapping = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def normalize_status(raw: str) -> str:
    return STATUS_MAP.get(raw.strip().lower(), "applied")


def parse_date(raw: str):
    if not raw or not raw.strip():
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_salary(raw: str):
    if not raw or not raw.strip():
        return None
    try:
        cleaned = raw.strip().replace(",", "").replace("$", "").replace("k", "000").split(".")[0]
        return int(cleaned)
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/applications")
async def import_applications(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    content = await file.read()
    # utf-8-sig strips the BOM that Excel adds to CSV exports
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    headers = list(reader.fieldnames or [])
    col_map = detect_columns(headers)

    if "role_title" not in col_map:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Could not find a job title column. "
                f"Headers found: {headers}. "
                f"Expected one of: title, job_title, role, position."
            ),
        )

    created = 0
    skipped = 0
    errors = []
    company_cache: dict = {}  # name → id, avoids duplicate DB lookups

    for row_num, row in enumerate(reader, start=2):
        try:
            role_title = row.get(col_map.get("role_title", ""), "").strip()
            if not role_title:
                skipped += 1
                continue

            # --- Company: find existing or create new ---
            comp_id = None
            if "company" in col_map:
                company_name = row.get(col_map["company"], "").strip()
                if company_name:
                    if company_name in company_cache:
                        comp_id = company_cache[company_name]
                    else:
                        existing = db.query(models.Company).filter(
                            models.Company.name == company_name
                        ).first()
                        if existing:
                            comp_id = existing.id
                        else:
                            new_co = models.Company(name=company_name)
                            db.add(new_co)
                            db.flush()  # get the id without full commit
                            comp_id = new_co.id
                        company_cache[company_name] = comp_id

            # --- Other fields ---
            status = normalize_status(row.get(col_map.get("status", ""), "applied"))
            date_applied = parse_date(row.get(col_map.get("date_applied", ""), ""))
            job_link = row.get(col_map.get("job_link", ""), "").strip() or None if "job_link" in col_map else None
            source = row.get(col_map.get("source", ""), "").strip() or None if "source" in col_map else None
            notes = row.get(col_map.get("notes", ""), "").strip() or None if "notes" in col_map else None
            salary_min = parse_salary(row.get(col_map.get("salary_min", ""), "")) if "salary_min" in col_map else None
            salary_max = parse_salary(row.get(col_map.get("salary_max", ""), "")) if "salary_max" in col_map else None

            application = models.Application(
                company_id=comp_id,
                role_title=role_title,
                status=status,
                job_link=job_link,
                date_applied=date_applied,
                source=source,
                salary_min=salary_min,
                salary_max=salary_max,
                notes=notes,
            )
            db.add(application)
            db.commit()
            created += 1

        except Exception as e:
            db.rollback()
            errors.append({"row": row_num, "error": str(e)})
            skipped += 1

    return {
        "created": created,
        "skipped": skipped,
        "errors": errors[:20],
        "columns_detected": col_map,
    }
