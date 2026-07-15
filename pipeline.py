"""This file runs the full assignment pipeline from ingestion to report."""

import asyncio
import json
import logging
from pathlib import Path

from collation import build_collated_underwriting_view
from features.build_features import build_feature_rows
from model.risk_model import aggregate_portfolio_risk, train_risk_model
from reporting.llm_report import generate_underwriting_report


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOGGER = logging.getLogger(__name__)


async def run_pipeline(mock_api_base_url: str = "http://127.0.0.1:8000") -> dict:
    """Run every assignment step and write inspectable output files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Starting merchant underwriting pipeline.")
    collated = await build_collated_underwriting_view(mock_api_base_url=mock_api_base_url)
    LOGGER.info("Collated %s merchant rows.", len(collated["rows"]))

    feature_rows = build_feature_rows(collated["rows"])
    LOGGER.info("Built %s model feature rows.", len(feature_rows))

    model_output = train_risk_model(feature_rows)
    LOGGER.info("Trained %s model.", model_output["model_type"])

    portfolio_summary = aggregate_portfolio_risk(model_output["scored_rows"])
    LOGGER.info("Aggregated portfolio risk summary.")

    pipeline_output = {
        "collated": collated,
        "features": feature_rows,
        "model": model_output,
        "portfolio": portfolio_summary,
    }
    report_result = generate_underwriting_report(pipeline_output, output_dir=OUTPUT_DIR)
    LOGGER.info("Report generation status: %s.", report_result["status"])

    pipeline_output["report_result"] = report_result
    (OUTPUT_DIR / "pipeline_output.json").write_text(
        json.dumps(pipeline_output, indent=2),
        encoding="utf-8",
    )
    LOGGER.info("Pipeline output written to %s.", OUTPUT_DIR / "pipeline_output.json")
    return pipeline_output


def main():
    """Run the async pipeline from the command line."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    output = asyncio.run(run_pipeline())
    print(json.dumps(output["portfolio"], indent=2))
    print(json.dumps(output["report_result"], indent=2))


if __name__ == "__main__":
    main()
