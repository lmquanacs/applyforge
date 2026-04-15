from __future__ import annotations

from pathlib import Path

import pdfplumber
from docx import Document


def extract(path: str | Path) -> str:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(p)
    if suffix == ".docx":
        return _extract_docx(p)
    if suffix in (".md", ".txt"):
        return p.read_text(encoding="utf-8")

    raise ValueError(f"Unsupported file format: {suffix}")


def _extract_pdf(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]

    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(
            f"No text found in '{path}'. The PDF may be image-based. "
            "Please run OCR first or provide a text-based PDF."
        )
    return text


def _extract_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
