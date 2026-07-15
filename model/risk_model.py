"""This file trains a small explainable risk model and summarizes portfolio risk."""

from typing import Any

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


NUMERIC_FEATURES = ["monthly_volume", "transaction_count", "dispute_count", "dispute_rate"]
CATEGORICAL_FEATURES = ["volume_band", "country_region", "internal_risk_flag"]


def train_risk_model(feature_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Train a simple logistic regression model on merchant feature rows.

    Logistic regression is intentionally simple: it is easier to explain in an
    interview than a complex model, which matters for a small take-home dataset.
    """
    X = [
        {feature: row[feature] for feature in NUMERIC_FEATURES + CATEGORICAL_FEATURES}
        for row in feature_rows
    ]
    y = [row["target_high_dispute_risk"] for row in feature_rows]

    # DictVectorizer is a good fit here because our feature rows are plain
    # dictionaries. It turns text categories into one-hot numeric columns and
    # keeps numeric values as numeric model inputs.
    preprocessor = DictVectorizer(sparse=False)
    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )

    # The dataset is tiny, so metrics are directional. They prove the code path
    # works; they are not claims of production-grade predictive power.
    stratify = y if len(set(y)) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )
    model.fit(X_train, y_train)
    probabilities = [float(prob[1]) for prob in model.predict_proba(X)]
    test_predictions = model.predict(X_test)

    metrics = {"accuracy": float(accuracy_score(y_test, test_predictions))}
    if len(set(y_test)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))
    else:
        metrics["roc_auc"] = None

    scored_rows = []
    for row, probability in zip(feature_rows, probabilities):
        scored_row = dict(row)
        scored_row["predicted_high_risk_probability"] = round(probability, 4)
        scored_row["model_risk_band"] = _risk_band(probability)
        scored_rows.append(scored_row)

    return {
        "model_type": "logistic_regression",
        "metrics": metrics,
        "scored_rows": scored_rows,
    }


def _risk_band(probability: float) -> str:
    """Convert a model probability into a human-friendly risk band."""
    if probability >= 0.65:
        return "high"
    if probability >= 0.35:
        return "medium"
    return "low"


def aggregate_portfolio_risk(scored_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize merchant-level scores into a portfolio-level risk view."""
    expected_high_risk_count = sum(row["predicted_high_risk_probability"] for row in scored_rows)
    expected_loss = sum(
        row["predicted_high_risk_probability"] * row["monthly_volume"] * 0.01
        for row in scored_rows
    )
    high_band_count = sum(1 for row in scored_rows if row["model_risk_band"] == "high")

    return {
        "merchant_count": len(scored_rows),
        "expected_high_risk_count": round(expected_high_risk_count, 2),
        "high_risk_band_count": high_band_count,
        "simple_expected_loss": round(expected_loss, 2),
        "expected_loss_assumption": "probability * monthly_volume * 1% loss rate",
    }
