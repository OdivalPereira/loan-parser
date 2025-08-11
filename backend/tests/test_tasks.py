from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import Base
from backend import tasks
from backend.parsers import ParserNotFoundError
from fastapi import HTTPException
from backend.models import Contrato, Empresa, Extrato
import pytest


def _setup_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal


def test_parse_sicoob_invalid_contract(tmp_path, monkeypatch):
    Session = _setup_db(tmp_path)
    monkeypatch.setattr(tasks, "SessionLocal", Session)
    monkeypatch.setattr(tasks, "parse", lambda *args, **kwargs: {"header": [], "transactions": []})

    pdf_path = Path(tmp_path) / "dummy.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    result = tasks.parse_sicoob(str(pdf_path), contract_id=999)
    assert result["status"] == "erro"

    session = Session()
    extratos = session.query(Extrato).all()
    session.close()

    assert len(extratos) == 1
    assert extratos[0].contrato_id is None


def test_parse_sicoob_persists_data(tmp_path, monkeypatch):
    Session = _setup_db(tmp_path)
    monkeypatch.setattr(tasks, "SessionLocal", Session)

    # create required Empresa and Contrato
    session = Session()
    empresa = Empresa(nome="ACME", cnpj="123")
    session.add(empresa)
    session.flush()
    contrato = Contrato(
        empresa_id=empresa.id,
        numero="1",
        banco="Sicoob",
        saldo=1000.0,
        taxa_anual=0.1,
        data_inicio=date(2023, 1, 1),
    )
    session.add(contrato)
    session.commit()
    contrato_id = contrato.id
    session.close()

    monkeypatch.setattr(
        tasks,
        "parse",
        lambda *args, **kwargs: {
            "header": ["Sicoob"],
            "transactions": [
                {
                    "data_ref": "01/01/2023",
                    "data_lanc": "01/01/2023",
                    "descricao": "x",
                    "valor_debito": None,
                    "valor_credito": 1.0,
                    "saldo": 1.0,
                }
            ],
        },
    )

    pdf_path = Path(tmp_path) / "dummy.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    result = tasks.parse_sicoob(str(pdf_path), contract_id=contrato_id)
    assert result["transactions"]

    session = Session()
    extratos = session.query(Extrato).all()
    session.close()

    assert len(extratos) == 1
    assert extratos[0].contrato_id == contrato_id


def test_parse_sicoob_unknown_parser(tmp_path, monkeypatch):
    Session = _setup_db(tmp_path)
    monkeypatch.setattr(tasks, "SessionLocal", Session)

    def fake_parse(*args, **kwargs):
        raise ParserNotFoundError("no parser")

    monkeypatch.setattr(tasks, "parse", fake_parse)

    pdf_path = Path(tmp_path) / "dummy.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    with pytest.raises(HTTPException) as exc_info:
        tasks.parse_sicoob(str(pdf_path), contract_id=None)

    assert exc_info.value.status_code == 404
