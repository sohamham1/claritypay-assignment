from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_submission_has_one_public_pipeline_script():
    scripts = sorted(path.name for path in (PROJECT_ROOT / "scripts").glob("run*.py"))

    assert scripts == ["run_pipeline.py"]


def test_readme_uses_single_public_pipeline_command():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "python scripts/run_pipeline.py" in text
    assert "run_part1_demo.py" not in text
    assert "run_part2_demo.py" not in text


def test_readme_maps_assignment_coverage():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    for term in [
        "Simulated API",
        "REST Countries",
        "CSV ingestion",
        "Async PDF ingestion",
        "ClarityPay website scrape",
        "LLM report generation",
        "AI usage documentation",
        "docs/AI_USAGE.md",
    ]:
        assert term in text


def test_ai_usage_doc_is_in_public_docs_folder():
    assert (PROJECT_ROOT / "docs" / "AI_USAGE.md").exists()
    assert not (PROJECT_ROOT / "AI_USAGE.md").exists()


def test_generated_underwriting_report_is_available_in_public_docs():
    report = PROJECT_ROOT / "docs" / "underwriting_report.md"
    text = report.read_text(encoding="utf-8")

    assert report.exists()
    assert "BNPL Underwriting Risk Report" in text
    assert "Recommended Underwriting Posture" in text


def test_default_llm_model_is_terra():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    report_code = (PROJECT_ROOT / "reporting" / "llm_report.py").read_text(
        encoding="utf-8"
    )

    assert "gpt-5.6-terra" in readme
    assert 'os.getenv("OPENAI_MODEL", "gpt-5.6-terra")' in report_code


def test_dotenv_setup_is_documented_and_not_committed():
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    run_script = (PROJECT_ROOT / "scripts" / "run_pipeline.py").read_text(
        encoding="utf-8"
    )
    rest_countries_code = (
        PROJECT_ROOT / "ingestion" / "rest_countries_client.py"
    ).read_text(encoding="utf-8")

    assert (PROJECT_ROOT / ".env.example").exists()
    assert "python-dotenv" in requirements
    assert ".env" in gitignore
    assert "load_dotenv" in run_script
    assert 'os.getenv("RESTCOUNTRIES_API_KEY") or DEMO_API_KEY' in rest_countries_code


def test_private_concepts_notes_are_not_public_submission_surface():
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/concepts_and_submission_notes.md" in gitignore
    assert "concepts_and_submission_notes.md" not in readme


def test_written_report_covers_governance_and_bnpl_risk():
    text = (PROJECT_ROOT / "docs" / "written_report.md").read_text(encoding="utf-8")

    for term in [
        "BNPL Risk Framing",
        "dispute risk",
        "counterparty/portfolio risk",
        "Governance Coverage",
        "Schema validation",
        "Idempotency",
        "model drift",
    ]:
        assert term in text


def test_decision_log_uses_professional_headings_not_part_labels():
    text = (PROJECT_ROOT / "docs" / "obstacles_and_decisions.md").read_text(
        encoding="utf-8"
    )

    assert "## Part 1" not in text
    assert "## Part 2" not in text
    assert "## API Contract Ambiguity" in text
