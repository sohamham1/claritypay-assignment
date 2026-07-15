"""This file extracts text from the sample PDF in an async-friendly way."""

import asyncio
from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF_PATH = PROJECT_ROOT / "data" / "sample_merchant_summary.pdf"


def _extract_pdf_text_sync(path: Path) -> str:
    """Extract readable text from the PDF using pdfplumber.

    PDF extraction is usually blocking file work. We keep the actual extraction
    in a normal function, then call it from an async wrapper below.
    """
    pypdf_text = _extract_pdf_text_with_pypdf(path)
    if pypdf_text:
        return pypdf_text

    page_text: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                page_text.append(text.strip())
    return "\n\n".join(page_text)


def _extract_pdf_text_with_pypdf(path: Path) -> str:
    """Try pypdf first because it extracts this sample PDF in cleaner order."""
    reader = PdfReader(path)
    page_text = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(text for text in page_text if text)


async def extract_pdf_text_async(path: Path = DEFAULT_PDF_PATH) -> dict[str, Any]:
    """Extract PDF text without blocking the rest of an async pipeline.

    In production this might be a background job or queue worker. For this
    assignment, `asyncio.to_thread` is a simple way to show the async pattern.
    """
    text = await asyncio.to_thread(_extract_pdf_text_sync, path)
    return {
        "source": "sample_merchant_summary_pdf",
        "status": "extracted" if text else "empty",
        "text": text,
        "character_count": len(text),
    }
