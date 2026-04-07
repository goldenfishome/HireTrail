from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/", response_model=schemas.InterviewOut, status_code=201)
def create_interview(interview: schemas.InterviewCreate, db: Session = Depends(get_db)):
    return crud.create_interview(db, interview)


@router.get("/", response_model=List[schemas.InterviewOut])
def list_interviews(
    skip: int = 0,
    limit: int = 100,
    application_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return crud.get_interviews(db, skip=skip, limit=limit, application_id=application_id)


@router.get("/{interview_id}", response_model=schemas.InterviewOut)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    db_interview = crud.get_interview(db, interview_id)
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return db_interview


@router.put("/{interview_id}", response_model=schemas.InterviewOut)
def update_interview(
    interview_id: int, interview: schemas.InterviewUpdate, db: Session = Depends(get_db)
):
    db_interview = crud.update_interview(db, interview_id, interview)
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return db_interview


@router.delete("/{interview_id}", response_model=schemas.InterviewOut)
def delete_interview(interview_id: int, db: Session = Depends(get_db)):
    db_interview = crud.delete_interview(db, interview_id)
    if not db_interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return db_interview
