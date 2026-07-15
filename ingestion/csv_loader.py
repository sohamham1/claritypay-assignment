"""This file loads merchant data from the CSV and checks that rows are usable."""

import csv
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MERCHANTS_CSV_PATH = PROJECT_ROOT / "data" / "merchants.csv"


class MerchantRecord(BaseModel):
    """A validated merchant row from the assignment CSV.

    The CSV reader starts with text values. This model converts numeric fields
    into real numbers and rejects rows that do not match the expected schema.
    """

    merchant_id: str
    name: str
    country: str
    registration_number: str = ""
    monthly_volume: float = Field(ge=0)
    dispute_count: int = Field(ge=0)
    transaction_count: int = Field(gt=0)

    @field_validator("merchant_id", "name", "country")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        """Reject important text fields if they are empty."""
        if not value or not value.strip():
            raise ValueError("field must not be blank")
        return value.strip()

    @field_validator("registration_number", mode="before")
    @classmethod
    def blank_registration_number_is_allowed(cls, value: Any) -> str:
        """Normalize missing registration numbers to an empty string."""
        return "" if value is None else str(value).strip()

    @property
    def dispute_rate(self) -> float:
        """Return disputes divided by transaction count for this merchant."""
        return self.dispute_count / self.transaction_count


def load_merchants_csv(path: Path = DEFAULT_MERCHANTS_CSV_PATH) -> list[MerchantRecord]:
    """Read the merchant CSV file and return validated merchant records.

    The merchant CSV is the base table for the assignment. Later steps enrich
    these same merchants with API, PDF, scrape, model, and report information.
    """
    valid_records, invalid_rows = load_merchants_csv_with_errors(path)
    if invalid_rows:
        row_numbers = ", ".join(str(row["row_number"]) for row in invalid_rows)
        raise ValueError(f"Invalid merchant rows found at CSV row(s): {row_numbers}")
    return valid_records


def load_merchants_csv_with_errors(path: Path = DEFAULT_MERCHANTS_CSV_PATH) -> tuple[list[MerchantRecord], list[dict]]:
    """Read merchant rows and keep invalid-row details for logging/tests."""
    required_columns = set(MerchantRecord.model_fields)
    valid_records: list[MerchantRecord] = []
    invalid_rows: list[dict] = []

    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"Missing required CSV columns: {sorted(missing_columns)}")

        for row_number, row in enumerate(reader, start=2):
            try:
                valid_records.append(MerchantRecord.model_validate(row))
            except ValidationError as exc:
                # We keep the original row and error text so a data-quality issue
                # can be explained instead of silently dropped.
                invalid_rows.append(
                    {
                        "row_number": row_number,
                        "row": row,
                        "errors": exc.errors(),
                    }
                )

    return valid_records, invalid_rows
