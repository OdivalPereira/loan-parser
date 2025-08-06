from backend.parsers.sicoob import parse


def test_parse_returns_text(sample_pdf_bytes):
    result = parse(sample_pdf_bytes)
    assert "Test PDF 1" in result["raw_text"]
