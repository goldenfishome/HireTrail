import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


@pytest.fixture
def company_id():
    return client.post("/companies/", json={"name": "Test Company"}).json()["id"]


def test_create_application(company_id):
    response = client.post("/applications/", json={
        "company_id": company_id,
        "role_title": "Software Engineer",
        "status": "applied",
        "salary_min": 80000,
        "salary_max": 120000,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["role_title"] == "Software Engineer"
    assert data["status"] == "applied"


def test_create_application_invalid_status(company_id):
    response = client.post("/applications/", json={
        "company_id": company_id,
        "role_title": "Engineer",
        "status": "not_a_real_status",
    })
    assert response.status_code == 422


def test_create_application_invalid_salary(company_id):
    response = client.post("/applications/", json={
        "company_id": company_id,
        "role_title": "Engineer",
        "salary_min": 120000,
        "salary_max": 80000,
    })
    assert response.status_code == 422


def test_create_application_missing_required(company_id):
    response = client.post("/applications/", json={"company_id": company_id})
    assert response.status_code == 422


def test_filter_by_status(company_id):
    client.post("/applications/", json={"company_id": company_id, "role_title": "A", "status": "applied"})
    client.post("/applications/", json={"company_id": company_id, "role_title": "B", "status": "offer"})
    response = client.get("/applications/?status=applied")
    assert response.status_code == 200
    assert all(r["status"] == "applied" for r in response.json())


def test_filter_by_company(company_id):
    client.post("/applications/", json={"company_id": company_id, "role_title": "Dev"})
    response = client.get(f"/applications/?company_id={company_id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_update_application_status(company_id):
    app_id = client.post("/applications/", json={
        "company_id": company_id, "role_title": "Dev", "status": "applied"
    }).json()["id"]
    response = client.put(f"/applications/{app_id}", json={"status": "interviewing"})
    assert response.status_code == 200
    assert response.json()["status"] == "interviewing"


def test_delete_application(company_id):
    app_id = client.post("/applications/", json={
        "company_id": company_id, "role_title": "Dev"
    }).json()["id"]
    assert client.delete(f"/applications/{app_id}").status_code == 200
    assert client.get(f"/applications/{app_id}").status_code == 404
