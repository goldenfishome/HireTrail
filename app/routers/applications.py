from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas
from app.database import get_db
from app.models import ApplicationStatus

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/", response_model=schemas.ApplicationOut, status_code=201)
def create_application(application: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    return crud.create_application(db, application)


@router.get("/", response_model=List[schemas.ApplicationOut])
def list_applications(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ApplicationStatus] = None,
    company_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return crud.get_applications(
        db, skip=skip, limit=limit, status=status, company_id=company_id, sort_by=sort_by
    )


@router.get("/{application_id}", response_model=schemas.ApplicationOut)
def get_application(application_id: int, db: Session = Depends(get_db)):
    db_application = crud.get_application(db, application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application


@router.put("/{application_id}", response_model=schemas.ApplicationOut)
def update_application(
    application_id: int, application: schemas.ApplicationUpdate, db: Session = Depends(get_db)
):
    db_application = crud.update_application(db, application_id, application)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application


@router.delete("/{application_id}", response_model=schemas.ApplicationOut)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    db_application = crud.delete_application(db, application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application
