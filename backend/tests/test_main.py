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


def test_upload_requires_contract_id(tmp_path, monkeypatch):
    pdf = tmp_path / "file.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    monkeypatch.setattr("backend.main.storage_path", str(tmp_path))

    with pdf.open("rb") as f:
        response = client.post(
            "/uploads",
            files={"file": ("file.pdf", f, "application/pdf")},
        )

    assert response.status_code == 422


def test_upload_enqueues_with_contract_id(tmp_path, monkeypatch):
    pdf = tmp_path / "file.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    called: dict = {}

    def fake_enqueue(name, *args):
        called["name"] = name
        called["args"] = args

    monkeypatch.setattr("backend.main.queue.enqueue", fake_enqueue)
    monkeypatch.setattr("backend.main.storage_path", str(tmp_path))

    with pdf.open("rb") as f:
        response = client.post(
            "/uploads?contract_id=123",
            files={"file": ("file.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    assert called["name"] == "tasks.parse_sicoob"
    assert called["args"][1] == 123
