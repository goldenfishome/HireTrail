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
def application_id():
    company_id = client.post("/companies/", json={"name": "Test Co"}).json()["id"]
    return client.post("/applications/", json={
        "company_id": company_id,
        "role_title": "Engineer",
        "status": "interviewing",
    }).json()["id"]


def test_create_interview(application_id):
    response = client.post("/interviews/", json={
        "application_id": application_id,
        "round_name": "Phone Screen",
        "interviewer_name": "Jane Smith",
        "result": "pending",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["round_name"] == "Phone Screen"
    assert data["result"] == "pending"
    assert data["application_id"] == application_id


def test_create_interview_empty_round_name(application_id):
    response = client.post("/interviews/", json={
        "application_id": application_id,
        "round_name": "",
    })
    assert response.status_code == 422


def test_create_interview_invalid_result(application_id):
    response = client.post("/interviews/", json={
        "application_id": application_id,
        "round_name": "Technical",
        "result": "not_a_result",
    })
    assert response.status_code == 422


def test_get_interview_by_id(application_id):
    interview_id = client.post("/interviews/", json={
        "application_id": application_id,
        "round_name": "Technical Round",
    }).json()["id"]
    response = client.get(f"/interviews/{interview_id}")
    assert response.status_code == 200
    assert response.json()["round_name"] == "Technical Round"


def test_get_interview_not_found():
    response = client.get("/interviews/9999")
    assert response.status_code == 404


def test_filter_interviews_by_application(application_id):
    client.post("/interviews/", json={"application_id": application_id, "round_name": "Round 1"})
    client.post("/interviews/", json={"application_id": application_id, "round_name": "Round 2"})
    response = client.get(f"/interviews/?application_id={application_id}")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_interview_result(application_id):
    interview_id = client.post("/interviews/", json={
        "application_id": application_id,
        "round_name": "Final Round",
        "result": "pending",
    }).json()["id"]
    response = client.put(f"/interviews/{interview_id}", json={"result": "passed"})
    assert response.status_code == 200
    assert response.json()["result"] == "passed"


def test_delete_interview(application_id):
    interview_id = client.post("/interviews/", json={
        "application_id": application_id,
        "round_name": "To Delete",
    }).json()["id"]
    assert client.delete(f"/interviews/{interview_id}").status_code == 200
    assert client.get(f"/interviews/{interview_id}").status_code == 404
