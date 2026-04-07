from fastapi import FastAPI
from app.database import engine, Base
from app.routers import companies, applications, interviews, imports

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HireTrail API",
    description="Track companies, job applications, and interviews during your job search.",
    version="1.0.0",
)

app.include_router(companies.router)
app.include_router(applications.router)
app.include_router(interviews.router)
app.include_router(imports.router)


@app.get("/")
def root():
    return {"message": "HireTrail API is running", "docs": "/docs"}
