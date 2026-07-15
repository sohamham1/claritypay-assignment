"""This file runs the local mock API for internal merchant risk data.

The assignment asks us to pretend there is an internal ClarityPay service that
returns underwriting-style information. This FastAPI app is that fake service.
"""

import csv
from pathlib import Path

from fastapi import FastAPI, HTTPException


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MERCHANTS_CSV_PATH = PROJECT_ROOT / "data" / "merchants.csv"

app = FastAPI(title="Mock Merchant Risk API")


def _risk_flag(dispute_count: int, transaction_count: int) -> str:
    """Convert simple dispute behavior into a low/medium/high mock risk flag."""
    dispute_rate = dispute_count / transaction_count if transaction_count else 0
    if dispute_count >= 5 or dispute_rate >= 0.002:
        return "high"
    if dispute_count >= 2 or dispute_rate >= 0.001:
        return "medium"
    return "low"


def _load_mock_merchant_risk() -> dict:
    """Build mock API records from the provided merchant IDs.

    This keeps the fake API aligned with the assignment CSV. In a real company,
    this data would come from an internal database or risk service instead.
    """
    records = {}
    if not MERCHANTS_CSV_PATH.exists():
        return records

    with MERCHANTS_CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            monthly_volume = float(row["monthly_volume"])
            transaction_count = int(row["transaction_count"])
            dispute_count = int(row["dispute_count"])
            avg_ticket_size = monthly_volume / transaction_count if transaction_count else 0

            records[row["merchant_id"]] = {
                "merchant_id": row["merchant_id"],
                "internal_risk_flag": _risk_flag(dispute_count, transaction_count),
                "transaction_summary": {
                    "last_30d_volume": monthly_volume,
                    "last_30d_txn_count": transaction_count,
                    "avg_ticket_size": round(avg_ticket_size, 2),
                },
                "last_review_date": "2026-07-14",
            }
    return records


MOCK_MERCHANT_RISK = _load_mock_merchant_risk()


@app.get("/health")
def health_check():
    """Return a tiny response that proves the API server is running."""
    return {"status": "ok"}


@app.get("/merchants/{merchant_id}")
def get_merchant_risk(merchant_id: str):
    """Return one merchant's internal risk payload.

    The response is one JSON object because that is what the assignment's JSON
    Schema contract describes.
    """
    merchant = MOCK_MERCHANT_RISK.get(merchant_id)
    if merchant is None:
        raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")
    return merchant
