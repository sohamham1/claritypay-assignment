"""This file respectfully scrapes public context from claritypay.com.

The scraper is intentionally conservative: it visits public pages, extracts
high-confidence BNPL underwriting context, and records failures instead of
crashing the underwriting pipeline.
"""

import re
import time
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_CLARITYPAY_URL = "https://www.claritypay.com/"
USER_AGENT = "claritypay-assignment-student/1.0 (educational take-home)"
MAX_PAGES = 25
REQUEST_DELAY_SECONDS = 0.25
ALLOWED_NEWS_DOMAINS = {
    "www.claritypay.com",
    "www.prnewswire.com",
    "finance.yahoo.com",
    "www.citybiz.co",
    "www.seatrade-cruise.com",
}
IMPORTANT_NEWSROOM_URLS = [
    "https://www.prnewswire.com/news-releases/claritypay-and-neuberger-berman-announce-1-billion-capital-purchase-program-302368109.html",
]
CLIENT_NAME_ALIASES = {
    "LaseyAway": "LaserAway",
    "LaseyAway Logo": "LaserAway",
    "Safe Streets logo": "Safe Streets",
    "Club Wyndham logo": "Club Wyndham",
    "Margaritaville Vacation Club logo": "Margaritaville Vacation Club",
}
KNOWN_CLIENT_NAMES = [
    "LaserAway",
    "Safe Streets",
    "Club Wyndham",
    "Margaritaville Vacation Club",
    "JetBlue",
    "Diamonds International",
]
KNOWN_ECOSYSTEM_PARTNERS = [
    "DR Bank",
    "EXL",
    "Neuberger Berman",
    "Skeps",
    "TransUnion",
]


def fetch_claritypay_html(url: str = DEFAULT_CLARITYPAY_URL, timeout_seconds: int = 20) -> str:
    """Download a public page with a clear User-Agent.

    A User-Agent tells the website who is making the request. This is part of
    respectful scraping because it avoids pretending to be a normal browser.
    """
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout_seconds)
    response.raise_for_status()
    return response.text


def normalize_public_claritypay_url(raw_url: str, base_url: str = DEFAULT_CLARITYPAY_URL) -> str | None:
    """Return a clean public ClarityPay URL, or None when a link should be skipped."""
    if raw_url.startswith(("mailto:", "tel:", "javascript:")):
        return None

    absolute_url = urljoin(base_url, raw_url)
    absolute_url, _fragment = urldefrag(absolute_url)
    parsed = urlparse(absolute_url)

    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc == "account.claritypay.com":
        return None
    if parsed.netloc != "www.claritypay.com":
        return None
    if "login" in parsed.path.lower():
        return None

    path = parsed.path.rstrip("/") or "/"
    return f"https://{parsed.netloc}{path}"


def discover_public_links(html: str, page_url: str) -> list[str]:
    """Find same-site public links from one HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        normalized = normalize_public_claritypay_url(tag["href"], base_url=page_url)
        if normalized and normalized not in links:
            links.append(normalized)
    return links


def discover_newsroom_article_links(html: str, page_url: str) -> list[str]:
    """Find public Newsroom article links without opening arbitrary sites."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        absolute_url = urljoin(page_url, tag["href"])
        absolute_url, _fragment = urldefrag(absolute_url)
        parsed = urlparse(absolute_url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc not in ALLOWED_NEWS_DOMAINS:
            continue
        if parsed.netloc == "www.claritypay.com":
            normalized = normalize_public_claritypay_url(absolute_url, base_url=page_url)
            if normalized and normalized not in links:
                links.append(normalized)
            continue
        if absolute_url not in links:
            links.append(absolute_url)
    return links


def _visible_text(soup: BeautifulSoup) -> str:
    """Return readable page text after removing script/style noise."""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def _stat(label: str, value: str, context: str, source_url: str) -> dict[str, str]:
    """Create one sourced public stat with enough context to use responsibly."""
    return {
        "label": label,
        "value": value,
        "context": context,
        "source_url": source_url,
    }


def _extract_stats(text: str, source_url: str) -> list[dict[str, str]]:
    """Extract only BNPL-underwriting-relevant public stats with context.

    We do not scrape every visible number. For this assignment, a number is
    useful only if it informs merchant economics, approval coverage, financing
    range, rollout footprint, operating scale, or funding capacity.
    """
    lower_text = text.lower()
    rules = [
        (
            "approval_coverage",
            "85% True Approvals",
            "Approval coverage claim for merchant financing conversion.",
            "85% true approvals" in lower_text,
        ),
        (
            "merchant_conversion_lift",
            "250% Increase in Conversion Rate",
            "Merchant conversion impact claim from ClarityPay business context.",
            "250% increase in conversion rate" in lower_text
            or "lift conversion by up to 250%" in lower_text,
        ),
        (
            "merchant_average_sale_lift",
            "200% Higher Average Sale Amount",
            "Merchant average-sale impact claim from ClarityPay business context.",
            "200% higher average sale amount" in lower_text,
        ),
        (
            "financing_range",
            "$50 to $50,000",
            "Consumer purchase/financing range relevant to merchant exposure.",
            bool(re.search(r"\$50\s+(?:to|-|through)\s+\$50,?000", text, re.I))
            or "$50-$50k" in lower_text,
        ),
        (
            "term_range",
            "6 weeks to 84 months",
            "Financing term range relevant to product and repayment-risk context.",
            bool(re.search(r"6\s+weeks\s+to\s+84\s+months", text, re.I)),
        ),
        (
            "term_range_travel",
            "6 weeks to 48 months",
            "JetBlue financing term range for travel purchase context.",
            bool(re.search(r"6\s+weeks\s+to\s+48\s+months", text, re.I)),
        ),
        (
            "term_range_introductory",
            "0% APR on terms up to 12 months",
            "Introductory JetBlue financing offer context.",
            bool(re.search(r"0%\s+APR.{0,100}up to\s+12\s+months", text, re.I)),
        ),
        (
            "merchant_rollout_footprint",
            "more than 125 stores",
            "Diamonds International rollout footprint relevant to merchant scale.",
            bool(re.search(r"more than\s+125\s+stores", text, re.I)),
        ),
        (
            "funding_capacity",
            "up to $1 billion",
            "Capital purchase program context for ClarityPay funding capacity.",
            bool(re.search(r"(?:up to|as much as)\s+\$1\s*billion", text, re.I)),
        ),
        (
            "transaction_scale",
            "millions of transactions",
            "Operating-scale claim relevant to platform maturity.",
            "millions of transactions" in lower_text,
        ),
    ]
    return [_stat(label, value, context, source_url) for label, value, context, present in rules if present]


def _extract_value_props(text: str) -> list[str]:
    """Pick out short phrases that describe ClarityPay's value proposition."""
    candidates = [
        "Pay Over Time",
        "clear fees",
        "lower payments",
        "Flexible payment plans",
        "smart credit solutions",
        "clear terms",
        "branded financing",
        "increase conversion",
        "higher average sale amount",
        "loyalty",
        "pre-approval",
    ]
    found = []
    lower_text = text.lower()
    for candidate in candidates:
        if candidate.lower() in lower_text and candidate not in found:
            found.append(candidate)
    return found


def _clean_logo_name(alt_text: str) -> str:
    """Turn useful logo alt text into a known organization name."""
    cleaned = " ".join(alt_text.split()).strip()
    cleaned = CLIENT_NAME_ALIASES.get(cleaned, cleaned)
    cleaned = re.sub(r"\s+logo$", "", cleaned, flags=re.I).strip()
    return CLIENT_NAME_ALIASES.get(cleaned, cleaned)


def _unique_names(names: list[str]) -> list[str]:
    """Return unique names while preserving their first-seen order."""
    unique: list[str] = []
    for name in names:
        if name and name not in unique:
            unique.append(name)
    return unique


def _extract_client_names(soup: BeautifulSoup, text: str) -> list[str]:
    """Extract merchant/client names from logo alt text and announcement copy."""
    names: list[str] = []
    ignored_alt_terms = [
        "claritypay",
        "google",
        "mockup",
        "checkmark",
        "stars",
        "t-shirt",
        "shopping trolley",
        "airplane",
        "laptop",
        "phone",
        "chat bubbles",
    ]
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        if not alt or any(term in alt.lower() for term in ignored_alt_terms):
            continue
        cleaned = _clean_logo_name(alt)
        if cleaned in KNOWN_CLIENT_NAMES:
            names.append(cleaned)

    for known_name in KNOWN_CLIENT_NAMES:
        if re.search(rf"\b{re.escape(known_name)}\b", text, re.I):
            names.append(known_name)
    return _unique_names(names)


def _extract_partner_names(text: str) -> list[str]:
    """Extract banks, funding, data, servicing, and infrastructure partners."""
    names = []
    for known_name in KNOWN_ECOSYSTEM_PARTNERS:
        if re.search(rf"\b{re.escape(known_name)}\b", text, re.I):
            names.append(known_name)
    return _unique_names(names)


def parse_claritypay_html(html: str, source_url: str = DEFAULT_CLARITYPAY_URL) -> dict[str, Any]:
    """Parse ClarityPay HTML into the structured fields required by the brief."""
    soup = BeautifulSoup(html, "html.parser")
    text = _visible_text(soup)
    title_tag = soup.find("title")
    description_tag = soup.find("meta", attrs={"name": "description"})
    title = title_tag.get_text(" ", strip=True) if title_tag else ""
    description = ""
    if description_tag and description_tag.get("content"):
        description = description_tag["content"].strip()

    return {
        "source": "claritypay_website",
        "source_url": source_url,
        "status": "parsed",
        "title": title,
        "description": description,
        "value_propositions": _extract_value_props(f"{description} {text}"),
        "client_names": _extract_client_names(soup, text),
        "partner_names": _extract_partner_names(text),
        "public_stats": _extract_stats(text, source_url),
        "discovered_links": discover_public_links(html, source_url),
        "newsroom_article_links": discover_newsroom_article_links(html, source_url),
    }


def _unique_extend(existing: list[str], new_values: list[str]) -> list[str]:
    """Append new strings while preserving order and avoiding duplicates."""
    for value in new_values:
        if value and value not in existing:
            existing.append(value)
    return existing


def _unique_stat_extend(
    existing: list[dict[str, str]],
    new_values: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Append stat objects while avoiding duplicate label/value pairs.

    The same public fact often appears on multiple pages. For the underwriting
    report, one clearly sourced instance is cleaner than repeated copies.
    """
    seen = {(item["label"], item["value"]) for item in existing}
    for value in new_values:
        key = (value["label"], value["value"])
        if key not in seen:
            existing.append(value)
            seen.add(key)
    return existing


def scrape_claritypay(
    url: str = DEFAULT_CLARITYPAY_URL,
    max_pages: int = MAX_PAGES,
    request_delay_seconds: float = REQUEST_DELAY_SECONDS,
) -> dict[str, Any]:
    """Fetch and parse public ClarityPay website context from multiple pages.

    If the website is unavailable or changes shape, we return a fallback object
    so the rest of the pipeline can keep running.
    """
    start_url = normalize_public_claritypay_url(url) or DEFAULT_CLARITYPAY_URL.rstrip("/")
    queue = [start_url]
    visited_urls: list[str] = []
    failed_urls: list[dict[str, str]] = []
    page_summaries: list[dict[str, str]] = []
    value_propositions: list[str] = []
    client_names: list[str] = []
    partner_names: list[str] = []
    public_stats: list[dict[str, str]] = []

    while queue and len(visited_urls) < max_pages:
        current_url = queue.pop(0)
        if current_url in visited_urls:
            continue

        try:
            html = fetch_claritypay_html(current_url)
        except requests.RequestException as exc:
            failed_urls.append({"url": current_url, "reason": str(exc)})
            visited_urls.append(current_url)
            continue

        parsed = parse_claritypay_html(html, source_url=current_url)
        visited_urls.append(current_url)
        page_summaries.append(
            {
                "url": current_url,
                "title": parsed.get("title", ""),
                "description": parsed.get("description", ""),
            }
        )
        _unique_extend(value_propositions, parsed.get("value_propositions", []))
        _unique_extend(client_names, parsed.get("client_names", []))
        _unique_extend(partner_names, parsed.get("partner_names", []))
        _unique_stat_extend(public_stats, parsed.get("public_stats", []))

        discovered_links = parsed.get("discovered_links", [])
        if current_url.rstrip("/") == f"{DEFAULT_CLARITYPAY_URL.rstrip('/')}/news":
            discovered_links = (
                discovered_links
                + parsed.get("newsroom_article_links", [])
                + IMPORTANT_NEWSROOM_URLS
            )

        for discovered_url in discovered_links:
            if discovered_url not in visited_urls and discovered_url not in queue:
                queue.append(discovered_url)

        if request_delay_seconds:
            time.sleep(request_delay_seconds)

    if not page_summaries and failed_urls:
        return {
            "source": "claritypay_website",
            "source_url": url,
            "status": "fallback",
            "reason": "All website requests failed.",
            "description": "",
            "value_propositions": [],
            "client_names": [],
            "partner_names": [],
            "public_stats": [],
            "visited_urls": [],
            "failed_urls": failed_urls,
        }

    return {
        "source": "claritypay_website",
        "source_url": start_url,
        "status": "parsed" if page_summaries else "fallback",
        "description": page_summaries[0]["description"] if page_summaries else "",
        "page_summaries": page_summaries,
        "visited_urls": visited_urls,
        "failed_urls": failed_urls,
        "value_propositions": value_propositions,
        "client_names": client_names,
        "partner_names": partner_names,
        "public_stats": public_stats,
    }
