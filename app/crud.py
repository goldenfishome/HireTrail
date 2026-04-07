from sqlalchemy.orm import Session
from sqlalchemy import asc
from typing import Optional
from app import models, schemas


# --- Companies ---

def get_company(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()


def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()


def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


def update_company(db: Session, company_id: int, company: schemas.CompanyUpdate):
    db_company = get_company(db, company_id)
    if not db_company:
        return None
    for key, value in company.model_dump(exclude_unset=True).items():
        setattr(db_company, key, value)
    db.commit()
    db.refresh(db_company)
    return db_company


def delete_company(db: Session, company_id: int):
    db_company = get_company(db, company_id)
    if not db_company:
        return None
    db.delete(db_company)
    db.commit()
    return db_company


# --- Applications ---

def get_application(db: Session, application_id: int):
    return db.query(models.Application).filter(models.Application.id == application_id).first()


def get_applications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    company_id: Optional[int] = None,
    sort_by: Optional[str] = None,
):
    query = db.query(models.Application)
    if status:
        query = query.filter(models.Application.status == status)
    if company_id:
        query = query.filter(models.Application.company_id == company_id)
    if sort_by:
        col = getattr(models.Application, sort_by, None)
        if col is not None:
            query = query.order_by(asc(col))
    return query.offset(skip).limit(limit).all()


def create_application(db: Session, application: schemas.ApplicationCreate):
    db_application = models.Application(**application.model_dump())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


def update_application(db: Session, application_id: int, application: schemas.ApplicationUpdate):
    db_application = get_application(db, application_id)
    if not db_application:
        return None
    for key, value in application.model_dump(exclude_unset=True).items():
        setattr(db_application, key, value)
    db.commit()
    db.refresh(db_application)
    return db_application


def delete_application(db: Session, application_id: int):
    db_application = get_application(db, application_id)
    if not db_application:
        return None
    db.delete(db_application)
    db.commit()
    return db_application


# --- Interviews ---

def get_interview(db: Session, interview_id: int):
    return db.query(models.Interview).filter(models.Interview.id == interview_id).first()


def get_interviews(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    application_id: Optional[int] = None,
):
    query = db.query(models.Interview)
    if application_id:
        query = query.filter(models.Interview.application_id == application_id)
    return query.order_by(asc(models.Interview.interview_date)).offset(skip).limit(limit).all()


def create_interview(db: Session, interview: schemas.InterviewCreate):
    db_interview = models.Interview(**interview.model_dump())
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview


def update_interview(db: Session, interview_id: int, interview: schemas.InterviewUpdate):
    db_interview = get_interview(db, interview_id)
    if not db_interview:
        return None
    for key, value in interview.model_dump(exclude_unset=True).items():
        setattr(db_interview, key, value)
    db.commit()
    db.refresh(db_interview)
    return db_interview


def delete_interview(db: Session, interview_id: int):
    db_interview = get_interview(db, interview_id)
    if not db_interview:
        return None
    db.delete(db_interview)
    db.commit()
    return db_interview
