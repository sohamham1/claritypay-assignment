"""This file respectfully scrapes public context from claritypay.com.

The scraper is intentionally small and conservative: it visits public pages on
the ClarityPay site, extracts high-confidence fields, and records failures
instead of crashing the underwriting pipeline.
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


def fetch_claritypay_html(url: str = DEFAULT_CLARITYPAY_URL, timeout_seconds: int = 20) -> str:
    """Download the ClarityPay homepage HTML with a clear User-Agent.

    A User-Agent tells the website who is making the request. This is part of
    respectful scraping because it avoids pretending to be a normal browser.
    """
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout_seconds)
    response.raise_for_status()
    return response.text


def normalize_public_claritypay_url(raw_url: str, base_url: str = DEFAULT_CLARITYPAY_URL) -> str | None:
    """Return a clean public ClarityPay URL, or None when a link should be skipped.

    We skip account/login pages, non-web links, and external domains because the
    assignment asks for public ClarityPay website context, not authenticated user
    flows or unrelated third-party pages.
    """
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


def _visible_text(soup: BeautifulSoup) -> str:
    """Return readable page text after removing script/style noise."""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def _extract_stats(text: str) -> list[str]:
    """Find public-looking statistics such as dollar amounts or counts."""
    patterns = [
        r"\$[0-9]+(?:\.[0-9]+)?[BMK]?\+?\s+(?:Credit Issued|Loans Funded|Volume)",
        r"[0-9][0-9,]*(?:\.[0-9]+)?[BMK]?\+?\s+(?:Merchants|Monthly Transactions|Transactions|Customers)",
    ]
    stats: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text):
            cleaned = match.strip()
            if cleaned not in stats and any(char.isdigit() for char in cleaned):
                stats.append(cleaned)
    return stats[:10]


def _extract_value_props(text: str) -> list[str]:
    """Pick out short phrases that describe ClarityPay's value proposition."""
    candidates = [
        "Pay Over Time",
        "clear fees",
        "lower payments",
        "Flexible payment plans",
        "smart credit solutions",
        "clear terms",
    ]
    found = []
    lower_text = text.lower()
    for candidate in candidates:
        if candidate.lower() in lower_text and candidate not in found:
            found.append(candidate)
    return found


def _extract_partner_names(text: str) -> list[str]:
    """Extract partner names when the public site exposes obvious partner text.

    The current Webflow page may not expose logo alt text in a stable way, so
    this intentionally returns an empty list when partners are not obvious.
    """
    partner_match = re.search(r"(?:Proud Partner|Partners?|Trusted by)\s+(.{0,250})", text, re.I)
    if not partner_match:
        return []
    possible_names = re.split(r"\s{2,}|,|\|", partner_match.group(1))
    return [name.strip() for name in possible_names if 2 < len(name.strip()) < 60][:10]


def parse_claritypay_html(html: str, source_url: str = DEFAULT_CLARITYPAY_URL) -> dict[str, Any]:
    """Parse ClarityPay HTML into the structured fields required by the brief."""
    soup = BeautifulSoup(html, "html.parser")
    text = _visible_text(soup)
    description = ""
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(" ", strip=True)
    description_tag = soup.find("meta", attrs={"name": "description"})
    if description_tag and description_tag.get("content"):
        description = description_tag["content"].strip()

    return {
        "source": "claritypay_website",
        "source_url": source_url,
        "status": "parsed",
        "title": title,
        "description": description,
        "value_propositions": _extract_value_props(f"{description} {text}"),
        "partner_names": _extract_partner_names(text),
        "public_stats": _extract_stats(text),
        "discovered_links": discover_public_links(html, source_url),
    }


def _unique_extend(existing: list[str], new_values: list[str]) -> list[str]:
    """Append new strings while preserving order and avoiding duplicates."""
    for value in new_values:
        if value and value not in existing:
            existing.append(value)
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
    partner_names: list[str] = []
    public_stats: list[str] = []

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
        _unique_extend(partner_names, parsed.get("partner_names", []))
        _unique_extend(public_stats, parsed.get("public_stats", []))

        for discovered_url in parsed.get("discovered_links", []):
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
        "partner_names": partner_names,
        "public_stats": public_stats,
    }
