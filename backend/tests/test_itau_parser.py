import io
import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.itau import parse
import pytest


class DummyPage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self):
        return self._text


class DummyPDF:
    def __init__(self, text: str):
        self.pages = [DummyPage(text)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


TEXT_CONTENT = "\n".join(
    [
        "Itau",
        "Extrato de Conta Corrente",
        "Agencia: 1234 Conta: 56789-0",
        "Data Ref Data Lanc Descricao Valor Debito Valor Credito Saldo",
        "01/01/2023 01/01/2023 Deposito inicial - 1.000,00 1.000,00",
        "02/01/2023 02/01/2023 Saque 100,00 - 900,00",
    ]
)


def test_parse_text_pdf(monkeypatch):
    def fake_open(*args, **kwargs):
        return DummyPDF(TEXT_CONTENT)

    monkeypatch.setattr("parsers.itau.pdfplumber.open", fake_open)

    result = parse(io.BytesIO(b""))

    assert result["header"][0] == "Itau"
    assert len(result["transactions"]) == 2
    first = result["transactions"][0]
    assert first["data_ref"] == "01/01/2023"
    assert first["valor_credito"] == 1000.00
    second = result["transactions"][1]
    assert second["valor_debito"] == 100.00


def test_parse_image_pdf(monkeypatch):
    def fake_open(*args, **kwargs):
        return DummyPDF("")

    def fake_convert_from_bytes(*args, **kwargs):
        return [object()]

    def fake_image_to_string(*args, **kwargs):
        return TEXT_CONTENT

    monkeypatch.setattr("parsers.itau.pdfplumber.open", fake_open)
    monkeypatch.setattr("parsers.itau.convert_from_bytes", fake_convert_from_bytes)
    monkeypatch.setattr("parsers.itau.image_to_string", fake_image_to_string)

    def gen():
        yield b""

    result = parse(gen())

    assert len(result["transactions"]) == 2
    assert result["transactions"][0]["data_ref"] == "01/01/2023"


def test_parse_missing_header(monkeypatch):
    def fake_open(*args, **kwargs):
        return DummyPDF("irrelevant text")

    monkeypatch.setattr("parsers.itau.pdfplumber.open", fake_open)

    with pytest.raises(ValueError):
        parse(io.BytesIO(b""))


def test_parse_invalid_line(monkeypatch):
    text = "\n".join(
        [
            "Data Ref Data Lanc Descricao Valor Debito Valor Credito Saldo",
            "01/01/2023 01/01/2023 linha invalida",
        ]
    )

    def fake_open(*args, **kwargs):
        return DummyPDF(text)

    monkeypatch.setattr("parsers.itau.pdfplumber.open", fake_open)

    with pytest.raises(ValueError):
        parse(io.BytesIO(b""))
