from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date, datetime
from app.models import ApplicationStatus, InterviewResult


# --- Company ---

class CompanyBase(BaseModel):
    name: str
    website: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name must not be empty")
        return v.strip() if v else v


class CompanyOut(CompanyBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Application ---

class ApplicationBase(BaseModel):
    company_id: Optional[int] = None
    role_title: str
    status: ApplicationStatus = ApplicationStatus.wishlist
    job_link: Optional[str] = None
    date_applied: Optional[date] = None
    source: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("role_title")
    @classmethod
    def role_title_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("role_title must not be empty")
        return v.strip()


class ApplicationCreate(ApplicationBase):
    @model_validator(mode="after")
    def validate_salary_range(self) -> "ApplicationCreate":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min must be <= salary_max")
        return self


class ApplicationUpdate(BaseModel):
    role_title: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    job_link: Optional[str] = None
    date_applied: Optional[date] = None
    source: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_salary_range(self) -> "ApplicationUpdate":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min must be <= salary_max")
        return self


class ApplicationOut(ApplicationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Interview ---

class InterviewBase(BaseModel):
    application_id: int
    round_name: str
    interview_date: Optional[date] = None
    interviewer_name: Optional[str] = None
    result: InterviewResult = InterviewResult.pending
    notes: Optional[str] = None

    @field_validator("round_name")
    @classmethod
    def round_name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("round_name must not be empty")
        return v.strip()


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    round_name: Optional[str] = None
    interview_date: Optional[date] = None
    interviewer_name: Optional[str] = None
    result: Optional[InterviewResult] = None
    notes: Optional[str] = None


class InterviewOut(InterviewBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
