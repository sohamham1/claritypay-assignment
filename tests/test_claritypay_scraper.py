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
    <title>For Business</title>
    <meta name="description" content="ClarityPay offers smart credit solutions with clear fees and lower payments.">
  </head>
  <body>
    <h1>Pay Over Time</h1>
    <p>Flexible payment plans and branded financing that increase conversion.</p>
    <img alt="LaseyAway Logo">
    <img alt="Safe Streets logo">
    <img alt="Club Wyndham logo">
    <img alt="Margaritaville Vacation Club logo">
    <p>85% True Approvals</p>
    <p>250% Increase in Conversion Rate</p>
    <p>200% Higher Average Sale Amount</p>
    <p>Purchases from $50 to $50,000 with terms from 6 weeks to 84 months.</p>
    <p>Call 555-111-2222. Copyright 2026. NMLS 123456.</p>
    <p>Company annual sales: Less than $500K, $500K - $999K, $1MM - $9MM.</p>
  </body>
</html>
"""


def test_scraper_parser_extracts_underwriting_relevant_fields_from_html():
    result = parse_claritypay_html(SAMPLE_HTML, source_url="https://www.claritypay.com/for-business")

    assert result["status"] == "parsed"
    assert "Pay Over Time" in result["value_propositions"]
    assert "branded financing" in result["value_propositions"]
    assert result["client_names"] == [
        "LaserAway",
        "Safe Streets",
        "Club Wyndham",
        "Margaritaville Vacation Club",
    ]
    assert result["partner_names"] == []

    stats_by_label = {stat["label"]: stat for stat in result["public_stats"]}
    assert stats_by_label["approval_coverage"]["value"] == "85% True Approvals"
    assert stats_by_label["merchant_conversion_lift"]["value"] == "250% Increase in Conversion Rate"
    assert stats_by_label["merchant_average_sale_lift"]["value"] == "200% Higher Average Sale Amount"
    assert stats_by_label["financing_range"]["value"] == "$50 to $50,000"
    assert stats_by_label["term_range"]["value"] == "6 weeks to 84 months"
    assert all("source_url" in stat and "context" in stat for stat in result["public_stats"])

    stat_values = " ".join(stat["value"] for stat in result["public_stats"])
    assert "555-111-2222" not in stat_values
    assert "2026" not in stat_values
    assert "123456" not in stat_values
    assert "$500K" not in stat_values


def test_scraper_parser_extracts_clients_partners_and_newsroom_stats():
    html = """
    <html>
      <body>
        <p>JetBlue and ClarityPay launch personalized pay later program.</p>
        <p>Diamonds International and ClarityPay launch across more than 125 stores.</p>
        <p>Introductory 0% APR on terms up to 12 months.</p>
        <p>Payment options from 6 weeks to 48 months.</p>
        <p>Neuberger Berman announced up to $1 billion capital purchase program.</p>
        <p>DR Bank, EXL, Skeps, and TransUnion support the platform.</p>
        <p>Read time: 4 minutes. Published July 30, 2025.</p>
      </body>
    </html>
    """

    result = parse_claritypay_html(
        html,
        source_url="https://www.claritypay.com/announcements/example",
    )

    assert "JetBlue" in result["client_names"]
    assert "Diamonds International" in result["client_names"]
    for partner in ["DR Bank", "EXL", "Neuberger Berman", "Skeps", "TransUnion"]:
        assert partner in result["partner_names"]

    stats_by_label = {stat["label"]: stat for stat in result["public_stats"]}
    assert stats_by_label["merchant_rollout_footprint"]["value"] == "more than 125 stores"
    assert stats_by_label["term_range_introductory"]["value"] == "0% APR on terms up to 12 months"
    assert stats_by_label["term_range_travel"]["value"] == "6 weeks to 48 months"
    assert stats_by_label["funding_capacity"]["value"] == "up to $1 billion"

    stat_values = " ".join(stat["value"] for stat in result["public_stats"])
    assert "4 minutes" not in stat_values
    assert "July 30, 2025" not in stat_values


def test_scraper_returns_fallback_when_website_request_fails(monkeypatch):
    def fake_fetch(url):
        raise requests.Timeout("slow website")

    monkeypatch.setattr(claritypay_scraper, "fetch_claritypay_html", fake_fetch)

    result = scrape_claritypay()

    assert result["status"] == "fallback"
    assert result["value_propositions"] == []
    assert result["client_names"] == []
    assert result["partner_names"] == []


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
            <a href="/news">News</a>
            <h1>Pay Over Time</h1>
            <img alt="LaseyAway Logo">
        """,
        "https://www.claritypay.com/for-business": """
            <title>For Business</title>
            <meta name="description" content="Flexible payment plans for business partners.">
            <p>85% True Approvals</p>
            <p>DR Bank supports the lending platform.</p>
        """,
        "https://www.claritypay.com/news": """
            <title>Newsroom</title>
            <a href="/announcements/jetblue-example">JetBlue</a>
        """,
        "https://www.claritypay.com/announcements/jetblue-example": """
            <title>JetBlue announcement</title>
            <p>JetBlue and ClarityPay launch payment options from 6 weeks to 48 months.</p>
        """,
        "https://www.prnewswire.com/news-releases/claritypay-and-neuberger-berman-announce-1-billion-capital-purchase-program-302368109.html": """
            <title>Capital purchase program</title>
            <p>Neuberger Berman announced up to $1 billion capital purchase program.</p>
            <p>DR Bank, EXL, Skeps, and TransUnion supported the platform.</p>
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
        "https://www.claritypay.com/news",
        "https://www.claritypay.com/announcements/jetblue-example",
        "https://www.prnewswire.com/news-releases/claritypay-and-neuberger-berman-announce-1-billion-capital-purchase-program-302368109.html",
    ]
    assert "Pay Over Time" in result["value_propositions"]
    assert "LaserAway" in result["client_names"]
    assert "JetBlue" in result["client_names"]
    assert "DR Bank" in result["partner_names"]
    assert "Skeps" in result["partner_names"]
    assert "TransUnion" in result["partner_names"]
    assert any(stat["value"] == "85% True Approvals" for stat in result["public_stats"])
    assert any(stat["value"] == "6 weeks to 48 months" for stat in result["public_stats"])
    assert any(stat["value"] == "up to $1 billion" for stat in result["public_stats"])
