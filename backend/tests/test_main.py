import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app, get_db
from backend.db import Base


engine = create_engine(
    "sqlite:///./test.db", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_list_contracts_empty():
    response = client.get("/contracts")
    assert response.status_code == 200
    assert response.json() == []


def test_export_accruals_header_only():
    response = client.get("/accruals/export?start_date=2023-01-01&end_date=2023-01-31")
    assert response.status_code == 200
    assert "contract_id,principal,annual_rate,days,interest" in response.text
