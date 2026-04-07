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


def test_create_company():
    response = client.post("/companies/", json={"name": "Acme Corp", "location": "San Francisco"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["location"] == "San Francisco"
    assert "id" in data


def test_create_company_empty_name():
    response = client.post("/companies/", json={"name": ""})
    assert response.status_code == 422


def test_get_company_by_id():
    company_id = client.post("/companies/", json={"name": "Test Co"}).json()["id"]
    response = client.get(f"/companies/{company_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Co"


def test_get_company_not_found():
    response = client.get("/companies/9999")
    assert response.status_code == 404


def test_update_company():
    company_id = client.post("/companies/", json={"name": "Old Name"}).json()["id"]
    response = client.put(f"/companies/{company_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_company():
    company_id = client.post("/companies/", json={"name": "To Delete"}).json()["id"]
    assert client.delete(f"/companies/{company_id}").status_code == 200
    assert client.get(f"/companies/{company_id}").status_code == 404
