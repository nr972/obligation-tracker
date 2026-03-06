"""Document text extraction for PDF and DOCX files."""

from pathlib import Path


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    import fitz

    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages)


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file preserving paragraph structure."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        # Preserve heading structure with markers
        style_name = para.style.name if para.style else ""
        if style_name.startswith("Heading"):
            paragraphs.append(f"\n## {text}")
        else:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def parse_document(file_path: str) -> str:
    """Dispatch to the appropriate parser based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
