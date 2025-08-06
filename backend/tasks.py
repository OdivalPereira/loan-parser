from pathlib import Path

from .parsers import parse


def parse_sicoob(filepath: str) -> dict:
    """Parse a Sicoob PDF contract using the registered parser.

    If parsing fails, the contract is marked as "pendente revisão".
    """
    pdf_bytes = Path(filepath).read_bytes()
    try:
        return parse("sicoob", pdf_bytes)
    except Exception as exc:
        return {"status": "pendente revisão", "error": str(exc)}
