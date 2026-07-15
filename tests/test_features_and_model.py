from features.build_features import build_feature_rows, high_dispute_risk_target, volume_band
from model.risk_model import aggregate_portfolio_risk, train_risk_model


def _sample_collated_rows():
    rows = []
    for index in range(12):
        rows.append(
            {
                "merchant_id": f"M{index:03d}",
                "monthly_volume": 50000 + index * 10000,
                "transaction_count": 1000 + index * 100,
                "dispute_count": index % 6,
                "country_region": "Europe" if index % 2 == 0 else "Americas",
                "internal_risk_flag": ["low", "medium", "high"][index % 3],
            }
        )
    return rows


def test_feature_helpers_create_explainable_values():
    assert volume_band(20000) == "small"
    assert volume_band(90000) == "medium"
    assert volume_band(180000) == "large"
    assert high_dispute_risk_target(3, 2000) == 1
    assert high_dispute_risk_target(0, 2000) == 0


def test_build_feature_rows_adds_dispute_rate_and_target():
    feature_rows = build_feature_rows(_sample_collated_rows())

    assert feature_rows[0]["dispute_rate"] == 0
    assert "target_high_dispute_risk" in feature_rows[0]


def test_model_training_returns_scored_merchants_and_metrics():
    feature_rows = build_feature_rows(_sample_collated_rows())
    model_output = train_risk_model(feature_rows)

    assert model_output["model_type"] == "logistic_regression"
    assert len(model_output["scored_rows"]) == len(feature_rows)
    assert "accuracy" in model_output["metrics"]


def test_portfolio_aggregation_returns_expected_summary():
    scored_rows = [
        {"predicted_high_risk_probability": 0.5, "monthly_volume": 100000, "model_risk_band": "medium"},
        {"predicted_high_risk_probability": 0.8, "monthly_volume": 50000, "model_risk_band": "high"},
    ]

    summary = aggregate_portfolio_risk(scored_rows)

    assert summary["merchant_count"] == 2
    assert summary["expected_high_risk_count"] == 1.3
    assert summary["high_risk_band_count"] == 1
