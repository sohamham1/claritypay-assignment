"""This file generates or prepares the LLM underwriting report."""

import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"


def _report_context(pipeline_output: dict[str, Any]) -> dict[str, Any]:
    """Keep the LLM input focused on the most useful report context.

    The full pipeline output is saved separately as JSON. The report prompt gets
    a compact version so the LLM sees the key evidence without repeated noise.
    """
    scored_rows = pipeline_output.get("model", {}).get("scored_rows", [])
    top_risk_merchants = sorted(
        scored_rows,
        key=lambda row: row.get("predicted_high_risk_probability", 0),
        reverse=True,
    )[:10]
    collated = pipeline_output.get("collated", {})
    first_row = (collated.get("rows") or [{}])[0]
    return {
        "model_framing": {
            "target": (
                "target_high_dispute_risk is an assignment heuristic: 1 when "
                "dispute_count >= 3 or dispute_rate >= 0.0015."
            ),
            "target_leakage_control": (
                "dispute_count and dispute_rate are retained for reporting and "
                "target creation, but excluded from model input features."
            ),
            "model_input_features": [
                "monthly_volume",
                "transaction_count",
                "volume_band",
                "country_region",
                "internal_risk_flag",
                "has_registration_number",
            ],
            "caveat": (
                "The dataset is small and the target is derived, so model metrics "
                "are directional rather than production-ready evidence."
            ),
        },
        "portfolio": pipeline_output.get("portfolio", {}),
        "model_metrics": pipeline_output.get("model", {}).get("metrics", {}),
        "source_summaries": collated.get("source_summaries", {}),
        "top_risk_merchants": top_risk_merchants,
        "pdf_context_excerpt": first_row.get("pdf_context_excerpt", ""),
        "website_value_propositions": first_row.get("website_value_propositions", []),
        "website_client_names": first_row.get("website_client_names", []),
        "website_partner_names": first_row.get("website_partner_names", []),
        "website_public_stats": first_row.get("website_public_stats", []),
        "website_visited_urls": first_row.get("website_visited_urls", []),
    }


def build_underwriting_prompt(pipeline_output: dict[str, Any]) -> str:
    """Create the exact prompt that will be sent to the LLM.

    A prompt is the instruction package we give to the model. Here it includes
    the collated data, model outputs, and portfolio summary.
    """
    compact_payload = json.dumps(_report_context(pipeline_output), indent=2)
    return (
        "You are writing a concise underwriting report for a BNPL risk team.\n"
        "Use only the data provided below. Do not invent facts.\n"
        "Explain key merchant risks, model risk bands, portfolio-level risk, "
        "red flags, and production caveats.\n"
        "Mention the target-leakage control and small-data caveat when discussing "
        "model reliability.\n\n"
        f"Pipeline output:\n{compact_payload}\n"
    )


def generate_underwriting_report(
    pipeline_output: dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Generate an LLM report if an API key exists, otherwise save the prompt.

    We handle the no-key case honestly: the assignment asks for an LLM-generated
    report, so if no key exists we save the prompt artifact and mark the report
    as not generated instead of pretending.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_underwriting_prompt(pipeline_output)
    prompt_path = output_dir / "llm_report_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    if not os.getenv("OPENAI_API_KEY"):
        message = (
            "OPENAI_API_KEY is not set. Saved the exact LLM prompt, but did not "
            "generate a report."
        )
        report_path = output_dir / "underwriting_report.md"
        report_path.write_text(f"# Underwriting Report\n\n{message}\n", encoding="utf-8")
        return {
            "status": "prompt_saved_no_api_key",
            "prompt_path": str(prompt_path),
            "report_path": str(report_path),
            "message": message,
        }

    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    report_text = response.output_text
    report_path = output_dir / "underwriting_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    return {
        "status": "generated",
        "model": model,
        "prompt_path": str(prompt_path),
        "report_path": str(report_path),
    }
