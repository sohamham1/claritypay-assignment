"""This file enriches merchant countries using the REST Countries v5 API."""

import os
from functools import lru_cache
from typing import Any

import requests


REST_COUNTRIES_BASE_URL = "https://api.restcountries.com/countries/v5"
REST_COUNTRIES_SOURCE = "rest_countries_v5"
DEMO_API_KEY = "rc_live_demo"
COUNTRY_NAME_ALIASES = {
    "Czech Republic": "Czechia",
}


def _fallback_country_enrichment(country: str, reason: str) -> dict[str, Any]:
    """Return a safe country record when live enrichment is unavailable."""
    return {
        "country": country,
        "country_code": None,
        "region": "unknown",
        "subregion": "unknown",
        "source": REST_COUNTRIES_SOURCE,
        "status": "fallback",
        "reason": reason,
    }


def _get_api_key() -> str:
    """Read the REST Countries API key from the environment, or use the demo key."""
    return os.getenv("RESTCOUNTRIES_API_KEY") or DEMO_API_KEY


def _is_using_demo_key(api_key: str) -> bool:
    """Tell us whether the request is using the limited documentation demo key."""
    return api_key == DEMO_API_KEY


def _extract_objects(payload: Any) -> list[dict[str, Any]]:
    """Pull the country objects list out of the nested v5 API response."""
    if isinstance(payload, dict):
        data = payload.get("data", {})
        objects = data.get("objects", [])
        return objects if isinstance(objects, list) else []
    return []


def _normalize_country_object(country: str, country_object: dict[str, Any]) -> dict[str, Any]:
    """Convert the large REST Countries response into the few fields we need."""
    names = country_object.get("names", {})
    codes = country_object.get("codes", {})

    return {
        "country": names.get("common") or country,
        "country_code": codes.get("alpha_2"),
        "region": country_object.get("region") or "unknown",
        "subregion": country_object.get("subregion") or "unknown",
        "source": REST_COUNTRIES_SOURCE,
        "status": "enriched",
    }


def parse_country_enrichment(country: str, payload: Any, using_demo_key: bool = False) -> dict[str, Any]:
    """Parse one REST Countries response into our normalized enrichment format."""
    if using_demo_key:
        return _fallback_country_enrichment(
            country,
            "REST Countries demo key returns example data only; set RESTCOUNTRIES_API_KEY for real enrichment.",
        )

    objects = _extract_objects(payload)
    if not objects:
        return _fallback_country_enrichment(country, "No matching country returned by REST Countries.")

    return _normalize_country_object(country, objects[0])


@lru_cache(maxsize=128)
def fetch_country_enrichment(
    country: str,
    timeout_seconds: int = 10,
    base_url: str = REST_COUNTRIES_BASE_URL,
) -> dict[str, Any]:
    """Fetch and normalize country metadata from REST Countries v5.

    The cache avoids calling the public API again and again for repeated country
    names like "United Kingdom".
    """
    api_key = _get_api_key()
    query_country = COUNTRY_NAME_ALIASES.get(country, country)
    url = f"{base_url.rstrip('/')}/names.common/{query_country}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.Timeout:
        return _fallback_country_enrichment(country, "REST Countries request timed out.")
    except requests.RequestException as exc:
        return _fallback_country_enrichment(country, f"REST Countries request failed: {exc}")

    result = parse_country_enrichment(
        query_country,
        response.json(),
        using_demo_key=_is_using_demo_key(api_key),
    )
    if result["status"] == "enriched":
        result["country"] = country
    return result
