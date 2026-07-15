from pathlib import Path

import pytest

from ingestion.csv_loader import load_merchants_csv, load_merchants_csv_with_errors


def test_csv_loader_reads_valid_assignment_merchants():
    merchants = load_merchants_csv()

    assert len(merchants) == 50
    assert merchants[0].merchant_id == "M001"
    assert merchants[0].monthly_volume == 125000


def test_csv_loader_rejects_missing_required_columns(tmp_path: Path):
    bad_csv = tmp_path / "missing_columns.csv"
    bad_csv.write_text("merchant_id,name\nM001,Test Merchant\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required CSV columns"):
        load_merchants_csv(bad_csv)


def test_csv_loader_reports_invalid_numeric_rows(tmp_path: Path):
    bad_csv = tmp_path / "bad_numeric.csv"
    bad_csv.write_text(
        "merchant_id,name,country,registration_number,monthly_volume,dispute_count,transaction_count\n"
        "M001,Test Merchant,United Kingdom,,not-a-number,1,100\n",
        encoding="utf-8",
    )

    valid_rows, invalid_rows = load_merchants_csv_with_errors(bad_csv)

    assert valid_rows == []
    assert invalid_rows[0]["row_number"] == 2
    assert invalid_rows[0]["row"]["merchant_id"] == "M001"
