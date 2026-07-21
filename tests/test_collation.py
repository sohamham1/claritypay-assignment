import pytest

from collation import build_collated_underwriting_view


@pytest.mark.anyio
async def test_collation_returns_one_row_per_merchant(monkeypatch):
    monkeypatch.setattr("collation.fetch_internal_risk", lambda merchant_id, base_url: {
        "merchant_id": merchant_id,
        "internal_risk_flag": "low",
        "transaction_summary": {},
    })
    monkeypatch.setattr("collation.fetch_country_enrichment", lambda country: {
        "country": country,
        "country_code": "XX",
        "region": "Test Region",
        "subregion": "Test Subregion",
        "status": "enriched",
    })
    monkeypatch.setattr("collation.scrape_claritypay", lambda: {
        "status": "parsed",
        "value_propositions": ["Pay Over Time"],
        "client_names": ["JetBlue"],
        "partner_names": ["DR Bank"],
        "public_stats": [
            {
                "label": "approval_coverage",
                "value": "85% True Approvals",
                "context": "Approval coverage claim.",
                "source_url": "https://www.claritypay.com/for-business",
            }
        ],
    })
    async def fake_pdf():
        return {"status": "extracted", "text": "PDF text"}
    monkeypatch.setattr("collation.extract_pdf_text_async", fake_pdf)

    result = await build_collated_underwriting_view()

    assert len(result["rows"]) == 50
    assert result["rows"][0]["country_region"] == "Test Region"
    assert result["rows"][0]["website_client_names"] == ["JetBlue"]
    assert result["rows"][0]["website_partner_names"] == ["DR Bank"]
    assert result["rows"][0]["website_public_stats"][0]["label"] == "approval_coverage"
    assert result["source_summaries"]["merchant_count"] == 50
