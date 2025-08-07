import io
import re
from typing import List, Dict, Optional

from pdf2image import convert_from_bytes
import pdfplumber
from pytesseract import image_to_string

from . import register


def _parse_currency(value: str) -> Optional[float]:
    """Convert Brazilian formatted currency to float.

    Returns ``None`` for empty fields represented by ``-``. Raises ``ValueError``
    for any other malformed value.
    """

    value = value.strip()
    if value in {"", "-"}:
        return None

    value = value.replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Valor monetário inválido: {value}") from exc


@register("sicoob")
def parse(pdf_bytes: bytes) -> Dict[str, List[Dict[str, Optional[float]]]]:
    """Parse Sicoob loan contract PDF bytes into structured data.

    The parser first attempts to extract text using pdfplumber. If the PDF
    contains only images, it falls back to OCR using Tesseract.
    """

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if not text.strip():
        images = convert_from_bytes(pdf_bytes)
        text = "\n".join(image_to_string(img, lang="por") for img in images)

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Locate the table header which contains the data labels
    header_idx = None
    for i, line in enumerate(lines):
        if re.search(r"data\s+ref", line, re.IGNORECASE) and re.search(
            r"data\s+lan", line, re.IGNORECASE
        ):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Cabeçalho da tabela não encontrado")

    header = lines[:header_idx]
    data_lines = lines[header_idx + 1 :]

    pattern = re.compile(
        r"^(?P<data_ref>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<data_lanc>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<descricao>.*?)\s+"
        r"(?P<valor_debito>-|[\d.,]+)\s+"
        r"(?P<valor_credito>-|[\d.,]+)\s+"
        r"(?P<saldo>[\d.,]+)$"
    )

    transactions: List[Dict[str, Optional[float]]] = []
    for line in data_lines:
        if not re.match(r"^\d{2}/\d{2}/\d{4}", line):
            # Ignore lines that do not start with a date
            continue

        match = pattern.match(line)
        if not match:
            raise ValueError(f"Linha de movimentação inválida: {line}")

        transactions.append(
            {
                "data_ref": match.group("data_ref"),
                "data_lanc": match.group("data_lanc"),
                "descricao": match.group("descricao").strip(),
                "valor_debito": _parse_currency(match.group("valor_debito")),
                "valor_credito": _parse_currency(match.group("valor_credito")),
                "saldo": _parse_currency(match.group("saldo")),
            }
        )

    if not transactions:
        raise ValueError("Nenhuma movimentação encontrada")

    return {"header": header, "transactions": transactions}
