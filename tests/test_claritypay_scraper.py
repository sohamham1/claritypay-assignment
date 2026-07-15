import requests

from ingestion import claritypay_scraper
from ingestion.claritypay_scraper import (
    discover_public_links,
    normalize_public_claritypay_url,
    parse_claritypay_html,
    scrape_claritypay,
)


SAMPLE_HTML = """
<html>
  <head>
    <meta name="description" content="ClarityPay offers smart credit solutions with clear fees and lower payments.">
  </head>
  <body>
    <h1>Pay Over Time</h1>
    <p>Flexible payment plans for the moments that matter.</p>
    <p>1900+ Merchants</p>
    <p>$1.2B+ Credit Issued</p>
  </body>
</html>
"""


def test_scraper_parser_extracts_structured_fields_from_html():
    result = parse_claritypay_html(SAMPLE_HTML)

    assert result["status"] == "parsed"
    assert "Pay Over Time" in result["value_propositions"]
    assert any("1900" in stat for stat in result["public_stats"])
    assert result["partner_names"] == []


def test_scraper_returns_fallback_when_website_request_fails(monkeypatch):
    def fake_fetch(url):
        raise requests.Timeout("slow website")

    monkeypatch.setattr(claritypay_scraper, "fetch_claritypay_html", fake_fetch)

    result = scrape_claritypay()

    assert result["status"] == "fallback"
    assert result["value_propositions"] == []


def test_scraper_discovers_and_filters_public_same_site_links():
    html = """
    <a href="/for-business">Business</a>
    <a href="https://account.claritypay.com/login">Login</a>
    <a href="mailto:test@example.com">Email</a>
    <a href="https://example.com/">External</a>
    """

    links = discover_public_links(html, "https://www.claritypay.com/")

    assert links == ["https://www.claritypay.com/for-business"]
    assert normalize_public_claritypay_url("https://account.claritypay.com/login") is None
    assert normalize_public_claritypay_url("http://www.claritypay.com/faqs") == "https://www.claritypay.com/faqs"


def test_scraper_aggregates_multiple_mocked_pages(monkeypatch):
    pages = {
        "https://www.claritypay.com/": """
            <title>Home</title>
            <meta name="description" content="ClarityPay offers smart credit solutions.">
            <a href="/for-business">For Business</a>
            <h1>Pay Over Time</h1>
        """,
        "https://www.claritypay.com/for-business": """
            <title>For Business</title>
            <meta name="description" content="Flexible payment plans for business partners.">
            <p>$1.2B+ Credit Issued</p>
        """,
    }

    def fake_fetch(url):
        return pages[url]

    monkeypatch.setattr(claritypay_scraper, "fetch_claritypay_html", fake_fetch)

    result = scrape_claritypay(request_delay_seconds=0)

    assert result["status"] == "parsed"
    assert result["visited_urls"] == [
        "https://www.claritypay.com/",
        "https://www.claritypay.com/for-business",
    ]
    assert "Pay Over Time" in result["value_propositions"]
    assert "$1.2B+ Credit Issued" in result["public_stats"]
