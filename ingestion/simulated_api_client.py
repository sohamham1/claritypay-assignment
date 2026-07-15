"""This file calls the local mock API and validates the response contract."""

import json
from pathlib import Path

import requests
from jsonschema import FormatChecker, ValidationError, validate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = PROJECT_ROOT / "data" / "simulated_api_contract.json"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def load_contract(contract_path: Path = DEFAULT_CONTRACT_PATH) -> dict:
    """Read the JSON Schema file that defines the expected API response shape."""
    with contract_path.open("r", encoding="utf-8") as contract_file:
        return json.load(contract_file)


def validate_merchant_risk_payload(
    payload: dict,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
) -> dict:
    """Check that a mock API response follows the assignment contract."""
    contract = load_contract(contract_path)
    validate(instance=payload, schema=contract, format_checker=FormatChecker())
    return payload


def fetch_internal_risk(
    merchant_id: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: int = 10,
) -> dict:
    """Call the mock API for one merchant and return validated JSON data."""
    url = f"{base_url.rstrip('/')}/merchants/{merchant_id}"
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return validate_merchant_risk_payload(response.json())
