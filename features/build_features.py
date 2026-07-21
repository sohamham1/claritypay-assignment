"""This file turns collated merchant data into model-ready features."""

from typing import Any


def volume_band(monthly_volume: float) -> str:
    """Group merchant volume into simple bands for an explainable model."""
    if monthly_volume >= 150000:
        return "large"
    if monthly_volume >= 60000:
        return "medium"
    return "small"


def high_dispute_risk_target(dispute_count: int, transaction_count: int) -> int:
    """Create the model target: 1 means high dispute risk, 0 means lower risk.

    This is a simple assignment-friendly target because we do not have a real
    historical label from ClarityPay. We document that limitation clearly.
    """
    dispute_rate = dispute_count / transaction_count if transaction_count else 0
    return int(dispute_count >= 3 or dispute_rate >= 0.0015)


def build_feature_rows(collated_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create one feature row per merchant for model training and scoring.

    The feature row keeps dispute_count and dispute_rate for reporting and for
    creating the target label. The model itself must not train on those two
    fields because they directly define the target.
    """
    feature_rows = []
    for row in collated_rows:
        dispute_rate = row["dispute_count"] / row["transaction_count"]
        registration_number = str(row.get("registration_number") or "").strip()
        feature_rows.append(
            {
                "merchant_id": row["merchant_id"],
                "monthly_volume": row["monthly_volume"],
                "transaction_count": row["transaction_count"],
                "dispute_count": row["dispute_count"],
                "dispute_rate": dispute_rate,
                "volume_band": volume_band(row["monthly_volume"]),
                "country_region": row.get("country_region", "unknown"),
                "internal_risk_flag": row.get("internal_risk_flag", "unknown"),
                # A missing registration number is not automatically invalid for
                # every country, but it is useful KYB/data-quality context.
                "has_registration_number": int(bool(registration_number)),
                "target_high_dispute_risk": high_dispute_risk_target(
                    row["dispute_count"],
                    row["transaction_count"],
                ),
            }
        )
    return feature_rows
