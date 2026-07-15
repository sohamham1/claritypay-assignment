"""This file combines all source data into one underwriting view."""

import logging
from typing import Any

from ingestion.claritypay_scraper import scrape_claritypay
from ingestion.csv_loader import MerchantRecord, load_merchants_csv
from ingestion.pdf_ingestion import extract_pdf_text_async
from ingestion.rest_countries_client import fetch_country_enrichment
from ingestion.simulated_api_client import fetch_internal_risk


LOGGER = logging.getLogger(__name__)


def _internal_risk_fallback(merchant_id: str, reason: str) -> dict[str, Any]:
    """Return safe internal-risk fields when the mock API cannot be reached."""
    return {
        "merchant_id": merchant_id,
        "internal_risk_flag": "unknown",
        "transaction_summary": {},
        "internal_risk_status": "fallback",
        "internal_risk_reason": reason,
    }


def _merge_merchant_sources(
    merchant: MerchantRecord,
    internal_risk: dict[str, Any],
    country_enrichment: dict[str, Any],
    pdf_context: dict[str, Any],
    website_context: dict[str, Any],
) -> dict[str, Any]:
    """Combine one merchant row with all enrichment sources."""
    return {
        "merchant_id": merchant.merchant_id,
        "name": merchant.name,
        "country": merchant.country,
        "registration_number": merchant.registration_number,
        "monthly_volume": merchant.monthly_volume,
        "dispute_count": merchant.dispute_count,
        "transaction_count": merchant.transaction_count,
        "dispute_rate": merchant.dispute_rate,
        "internal_risk_flag": internal_risk.get("internal_risk_flag", "unknown"),
        "internal_risk_status": internal_risk.get("internal_risk_status", "enriched"),
        "country_code": country_enrichment.get("country_code"),
        "country_region": country_enrichment.get("region", "unknown"),
        "country_subregion": country_enrichment.get("subregion", "unknown"),
        "country_enrichment_status": country_enrichment.get("status", "unknown"),
        "pdf_context_status": pdf_context.get("status", "unknown"),
        "pdf_context_excerpt": pdf_context.get("text", "")[:500],
        "website_context_status": website_context.get("status", "unknown"),
        "website_value_propositions": website_context.get("value_propositions", []),
        "website_public_stats": website_context.get("public_stats", []),
        "website_visited_urls": website_context.get("visited_urls", []),
    }


async def build_collated_underwriting_view(
    mock_api_base_url: str = "http://127.0.0.1:8000",
) -> dict[str, Any]:
    """Build the single structured dataset required by the assignment.

    Collation means taking all source outputs and lining them up by merchant so
    the model and report can use one consistent view.
    """
    merchants = load_merchants_csv()
    LOGGER.info("Loaded %s merchant records from CSV.", len(merchants))

    pdf_context = await extract_pdf_text_async()
    LOGGER.info("PDF extraction status: %s.", pdf_context.get("status"))

    website_context = scrape_claritypay()
    LOGGER.info("Website scrape status: %s.", website_context.get("status"))

    # Fetch each unique country once. This keeps the pipeline respectful of
    # public API rate limits and makes repeated countries faster.
    country_cache = {
        country: fetch_country_enrichment(country)
        for country in sorted({merchant.country for merchant in merchants})
    }
    LOGGER.info("Fetched country enrichment for %s unique countries.", len(country_cache))

    rows = []
    for merchant in merchants:
        try:
            internal_risk = fetch_internal_risk(
                merchant.merchant_id,
                base_url=mock_api_base_url,
            )
            internal_risk["internal_risk_status"] = "enriched"
        except Exception as exc:
            internal_risk = _internal_risk_fallback(merchant.merchant_id, str(exc))
            LOGGER.warning(
                "Internal risk fallback for merchant %s: %s",
                merchant.merchant_id,
                exc,
            )

        rows.append(
            _merge_merchant_sources(
                merchant,
                internal_risk,
                country_cache[merchant.country],
                pdf_context,
                website_context,
            )
        )

    return {
        "rows": rows,
        "source_summaries": {
            "merchant_count": len(rows),
            "pdf_status": pdf_context.get("status"),
            "website_status": website_context.get("status"),
            "country_statuses": sorted({row["country_enrichment_status"] for row in rows}),
            "internal_risk_statuses": sorted({row["internal_risk_status"] for row in rows}),
        },
    }
