import pytest
from fastapi.testclient import TestClient
from jsonschema import ValidationError

from ingestion.simulated_api_client import validate_merchant_risk_payload
from simulated_api.app import app


client = TestClient(app)


def test_health_returns_success():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_known_merchant_returns_success():
    response = client.get("/merchants/M001")
    payload = response.json()

    assert response.status_code == 200
    assert payload["merchant_id"] == "M001"


def test_unknown_merchant_returns_404():
    response = client.get("/merchants/UNKNOWN")

    assert response.status_code == 404


def test_merchant_response_has_required_fields():
    response = client.get("/merchants/M001")
    payload = response.json()

    assert "merchant_id" in payload
    assert "internal_risk_flag" in payload
    assert "transaction_summary" in payload


def test_internal_risk_flag_uses_allowed_values():
    response = client.get("/merchants/M001")
    payload = response.json()

    assert payload["internal_risk_flag"] in {"low", "medium", "high"}


def test_transaction_summary_has_valid_numeric_fields():
    response = client.get("/merchants/M001")
    summary = response.json()["transaction_summary"]

    assert isinstance(summary["last_30d_volume"], (int, float))
    assert isinstance(summary["last_30d_txn_count"], int)
    assert isinstance(summary["avg_ticket_size"], (int, float))
    assert summary["last_30d_volume"] >= 0
    assert summary["last_30d_txn_count"] >= 0
    assert summary["avg_ticket_size"] >= 0


def test_client_validation_accepts_contract_matching_payload():
    payload = client.get("/merchants/M001").json()

    validated_payload = validate_merchant_risk_payload(payload)

    assert validated_payload == payload


def test_client_validation_rejects_invalid_payload():
    invalid_payload = {
        "merchant_id": "M001",
        "internal_risk_flag": "risky",
        "transaction_summary": {
            "last_30d_volume": 125000,
            "last_30d_txn_count": 3420,
            "avg_ticket_size": 36.55,
        },
    }

    with pytest.raises(ValidationError):
        validate_merchant_risk_payload(invalid_payload)
