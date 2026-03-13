"""PDF text extraction using pypdf."""

from pypdf import PdfReader


def extract_text(path: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text
