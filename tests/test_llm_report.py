from reporting.llm_report import build_underwriting_prompt, generate_underwriting_report


def test_llm_prompt_includes_pipeline_output():
    prompt = build_underwriting_prompt(
        {
            "portfolio": {"merchant_count": 2},
            "collated": {
                "rows": [
                    {
                        "website_client_names": ["JetBlue"],
                        "website_partner_names": ["DR Bank"],
                        "website_public_stats": [
                            {
                                "label": "approval_coverage",
                                "value": "85% True Approvals",
                                "context": "Approval coverage claim.",
                                "source_url": "https://www.claritypay.com/for-business",
                            }
                        ],
                    }
                ]
            },
        }
    )

    assert "underwriting report" in prompt
    assert "merchant_count" in prompt
    assert "JetBlue" in prompt
    assert "DR Bank" in prompt
    assert "85% True Approvals" in prompt
    assert "target-leakage" in prompt.lower()
    assert "excluded from model input features" in prompt
    assert "has_registration_number" in prompt


def test_missing_openai_key_saves_prompt_and_placeholder_report(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = generate_underwriting_report(
        {"portfolio": {"merchant_count": 2}},
        output_dir=tmp_path,
    )

    assert result["status"] == "prompt_saved_no_api_key"
    assert (tmp_path / "llm_report_prompt.txt").exists()
    assert (tmp_path / "underwriting_report.md").exists()
