import pytest

from ingestion.pdf_ingestion import extract_pdf_text_async


@pytest.mark.anyio
async def test_async_pdf_extraction_returns_text():
    result = await extract_pdf_text_async()

    assert result["status"] == "extracted"
    assert result["character_count"] > 0
    assert isinstance(result["text"], str)
