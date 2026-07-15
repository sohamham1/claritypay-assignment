import requests

from ingestion import rest_countries_client
from ingestion.rest_countries_client import (
    fetch_country_enrichment,
    parse_country_enrichment,
)


def test_successful_v5_parsing():
    payload = {
        "data": {
            "objects": [
                {
                    "names": {"common": "United Kingdom"},
                    "codes": {"alpha_2": "GB"},
                    "region": "Europe",
                    "subregion": "Northern Europe",
                }
            ]
        }
    }

    result = parse_country_enrichment("United Kingdom", payload)

    assert result == {
        "country": "United Kingdom",
        "country_code": "GB",
        "region": "Europe",
        "subregion": "Northern Europe",
        "source": "rest_countries_v5",
        "status": "enriched",
    }


def test_demo_key_returns_fallback_instead_of_fake_enrichment():
    payload = {
        "data": {
            "_demo": {"message": "example object only"},
            "objects": [
                {
                    "names": {"common": "Canada"},
                    "codes": {"alpha_2": "CA"},
                    "region": "Americas",
                    "subregion": "North America",
                }
            ],
        }
    }

    result = parse_country_enrichment("United Kingdom", payload, using_demo_key=True)

    assert result["country"] == "United Kingdom"
    assert result["country_code"] is None
    assert result["status"] == "fallback"
    assert "demo key" in result["reason"]


def test_empty_results_return_fallback():
    result = parse_country_enrichment("Atlantis", {"data": {"objects": []}})

    assert result["country"] == "Atlantis"
    assert result["region"] == "unknown"
    assert result["subregion"] == "unknown"
    assert result["status"] == "fallback"


def test_bearer_token_header_is_sent(monkeypatch):
    fetch_country_enrichment.cache_clear()
    captured_headers = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "objects": [
                        {
                            "names": {"common": "Germany"},
                            "codes": {"alpha_2": "DE"},
                            "region": "Europe",
                            "subregion": "Western Europe",
                        }
                    ]
                }
            }

    def fake_get(url, headers, timeout):
        captured_headers.update(headers)
        return FakeResponse()

    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    monkeypatch.setattr(rest_countries_client.requests, "get", fake_get)

    result = fetch_country_enrichment("Germany")

    assert captured_headers["Authorization"] == "Bearer test_key"
    assert result["country_code"] == "DE"


def test_timeout_returns_fallback(monkeypatch):
    fetch_country_enrichment.cache_clear()

    def fake_get(url, headers, timeout):
        raise requests.Timeout()

    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    monkeypatch.setattr(rest_countries_client.requests, "get", fake_get)

    result = fetch_country_enrichment("France")

    assert result["country"] == "France"
    assert result["status"] == "fallback"
    assert "timed out" in result["reason"]


def test_caching_fetches_same_country_once(monkeypatch):
    fetch_country_enrichment.cache_clear()
    calls = {"count": 0}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "objects": [
                        {
                            "names": {"common": "Germany"},
                            "codes": {"alpha_2": "DE"},
                            "region": "Europe",
                            "subregion": "Western Europe",
                        }
                    ]
                }
            }

    def fake_get(url, headers, timeout):
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    monkeypatch.setattr(rest_countries_client.requests, "get", fake_get)

    first = fetch_country_enrichment("Germany")
    second = fetch_country_enrichment("Germany")

    assert first == second
    assert calls["count"] == 1


def test_country_alias_keeps_original_country_name(monkeypatch):
    fetch_country_enrichment.cache_clear()
    requested_urls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "objects": [
                        {
                            "names": {"common": "Czechia"},
                            "codes": {"alpha_2": "CZ"},
                            "region": "Europe",
                            "subregion": "Central Europe",
                        }
                    ]
                }
            }

    def fake_get(url, headers, timeout):
        requested_urls.append(url)
        return FakeResponse()

    monkeypatch.setenv("RESTCOUNTRIES_API_KEY", "test_key")
    monkeypatch.setattr(rest_countries_client.requests, "get", fake_get)

    result = fetch_country_enrichment("Czech Republic")

    assert requested_urls[0].endswith("/names.common/Czechia")
    assert result["country"] == "Czech Republic"
    assert result["country_code"] == "CZ"
