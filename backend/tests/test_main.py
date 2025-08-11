import sys
from pathlib import Path
from datetime import date

sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app, get_db, get_current_user
from backend.db import Base
from backend.models import Empresa, Contrato, Extrato, Movimentacao


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


def override_current_user():
    return {"username": "admin"}


app.dependency_overrides[get_current_user] = override_current_user
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


def test_upload_rejects_non_pdf(tmp_path):
    txt = tmp_path / "file.txt"
    txt.write_text("not pdf")

    with txt.open("rb") as f:
        response = client.post(
            "/uploads?contract_id=123",
            files={"file": ("file.txt", f, "text/plain")},
        )

    assert response.status_code == 400


def test_upload_file_too_large(tmp_path, monkeypatch):
    pdf = tmp_path / "file.pdf"
    pdf.write_bytes(b"%PDF-1.4" + b"a" * 20)

    monkeypatch.setattr("backend.main.MAX_UPLOAD_SIZE", 10)
    monkeypatch.setattr("backend.main.storage_path", str(tmp_path))

    with pdf.open("rb") as f:
        response = client.post(
            "/uploads?contract_id=1",
            files={"file": ("file.pdf", f, "application/pdf")},
        )

    assert response.status_code == 413


def test_transactions_export_success():
    session = TestingSessionLocal()

    empresa = Empresa(nome="ACME", cnpj="123")
    session.add(empresa)
    session.flush()

    contrato = Contrato(
        empresa_id=empresa.id,
        numero="1",
        banco="Sicoob",
        saldo=0.0,
        taxa_anual=0.0,
        data_inicio=date(2023, 1, 1),
    )
    session.add(contrato)
    session.flush()

    extrato = Extrato(contrato_id=contrato.id, filepath="dummy", status="importado")
    session.add(extrato)
    session.flush()

    mov = Movimentacao(
        extrato_id=extrato.id,
        data_ref=date(2023, 1, 1),
        data_lanc=date(2023, 1, 1),
        descricao="juros recebidos",
        valor_debito=None,
        valor_credito=100.0,
        saldo=100.0,
    )
    session.add(mov)
    session.commit()

    empresa_id = empresa.id
    session.close()

    response = client.get(
        f"/transactions/export?empresa_id={empresa_id}&start_date=2023-01-01&end_date=2023-01-31"
    )

    assert response.status_code == 200
    assert "01/01/2023;631;111;100.00;juros recebidos" in response.text


def test_transactions_export_invalid_date():
    response = client.get(
        "/transactions/export?empresa_id=1&start_date=2023-02-01&end_date=2023-01-01"
    )

    assert response.status_code == 400


def test_contract_crud_and_extratos():
    session = TestingSessionLocal()
    empresa = Empresa(nome="NewCo", cnpj="999")
    session.add(empresa)
    session.commit()
    session.refresh(empresa)
    session.close()

    payload = {
        "empresa_id": empresa.id,
        "numero": "1",
        "bank": "Sicoob",
        "balance": 100.0,
        "cet": 0.1,
        "dueDate": "2023-01-01",
    }
    res = client.post("/contracts", json=payload)
    assert res.status_code == 201
    contract_id = res.json()["id"]

    res = client.put(f"/contracts/{contract_id}", json={"bank": "Itau"})
    assert res.status_code == 200
    assert res.json()["bank"] == "Itau"

    session = TestingSessionLocal()
    extrato = Extrato(contrato_id=int(contract_id), filepath="dummy", status="ok")
    session.add(extrato)
    session.commit()
    session.close()

    res = client.get(f"/contracts/{contract_id}/extratos")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.delete(f"/contracts/{contract_id}")
    assert res.status_code == 200
    assert res.json() == {"ok": True}
