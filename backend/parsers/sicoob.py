import io
from pdf2image import convert_from_bytes
import pdfplumber
from pytesseract import image_to_string

from . import register


@register("sicoob")
def parse(pdf_bytes: bytes) -> dict:
    """Parse Sicoob loan contract PDF bytes into structured data.

    The parser first attempts to extract text using pdfplumber. If the PDF
    contains only images, it falls back to OCR using Tesseract.
    """
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if not text.strip():
        images = convert_from_bytes(pdf_bytes)
        text = "\n".join(image_to_string(img, lang="por") for img in images)

    return {"raw_text": text.strip()}
