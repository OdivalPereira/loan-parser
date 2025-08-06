import pytest
from pathlib import Path


@pytest.fixture
def sample_pdf_path() -> Path:
    return Path(__file__).parent / "data" / "sample1.pdf"


@pytest.fixture
def sample_pdf_bytes(sample_pdf_path: Path) -> bytes:
    return sample_pdf_path.read_bytes()


@pytest.fixture
def another_pdf_path() -> Path:
    return Path(__file__).parent / "data" / "sample2.pdf"
