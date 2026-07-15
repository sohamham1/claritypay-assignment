# Merchant Underwriting Pipeline

Minimal production-style pipeline for the ClarityPay MLE take-home assignment.

The project ingests merchant data from multiple sources, validates and collates the data into one underwriting view, trains a simple risk model, aggregates portfolio risk, and prepares an LLM underwriting report from pipeline outputs.

## Assignment Coverage

| Requirement | Implementation |
| --- | --- |
| Simulated API | `simulated_api/`, `ingestion/simulated_api_client.py` |
| Real public API | `ingestion/rest_countries_client.py` using REST Countries v5 |
| CSV ingestion | `ingestion/csv_loader.py` |
| Async PDF ingestion | `ingestion/pdf_ingestion.py` |
| ClarityPay website scrape | `ingestion/claritypay_scraper.py` |
| Collated underwriting view | `collation.py` |
| Features, model, portfolio risk | `features/`, `model/` |
| LLM report generation | `reporting/llm_report.py` |
| Tests | `tests/` |
| AI usage documentation | `docs/AI_USAGE.md` |

## Repository Structure

```text
data/           Input data supplied with the assignment
ingestion/      Source readers and API/scrape clients
features/       Feature engineering
model/          Model training and portfolio aggregation
reporting/      LLM prompt and report generation
simulated_api/  Local mock API service
scripts/        Main pipeline entrypoint
tests/          Unit tests
docs/           Written report and engineering decisions
outputs/        Generated local outputs, ignored by Git
```

## Setup

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then edit `.env` with your local keys. For the live interview, this is the easiest setup because the pipeline loads these values automatically:

```text
RESTCOUNTRIES_API_KEY=your_rest_countries_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6-terra
```

`scripts/run_pipeline.py` loads `.env` automatically. The `.env` file is ignored by Git, so API keys stay local and should not be committed.

`RESTCOUNTRIES_API_KEY` enables real country enrichment. Without it, the REST Countries client returns a clearly marked fallback because the public demo key returns example data only.

`OPENAI_API_KEY` enables LLM report generation. With a real key in `.env`, the pipeline generates the underwriting report locally under `outputs/`.

`OPENAI_MODEL` is optional. The default is `gpt-5.6-terra`, chosen as a balanced model for a reviewer-facing underwriting report.

You can also set these values directly in PowerShell if you prefer. PowerShell environment variables override or supplement values from `.env`.

## Run The Pipeline

Start the mock API in one terminal:

```powershell
python -m uvicorn simulated_api.app:app --reload
```

In another terminal:

```powershell
python scripts/run_pipeline.py
```

Generated files are written to `outputs/`, which is intentionally ignored by Git. With both API keys present in `.env`, this run performs real REST Countries enrichment and generates the LLM underwriting report.

## Run Tests

```powershell
python -m pytest
```

## Governance And Checks

- CSV rows are validated with Pydantic before downstream use.
- Mock API responses are validated against the provided JSON Schema contract.
- REST Countries, website scraping, and mock API calls preserve status/fallback fields when data is unavailable.
- The ClarityPay scraper uses a clear User-Agent, timeout, page cap, and same-site public-link filtering.
- Generated outputs are ignored by Git to avoid committing local artifacts or prompt/report outputs accidentally.
- Idempotency in a production system would be handled with run IDs, deterministic output paths, and persisted source snapshots.
- Logging is kept lightweight in this take-home; production hardening would add structured logs, retries, and monitoring.

## Documentation

- `docs/written_report.md`: assumptions, tradeoffs, governance, and production improvements.
- `docs/underwriting_report.md`: generated underwriting report artifact from the credentialed pipeline run.
- `docs/obstacles_and_decisions.md`: material engineering decisions.
- `docs/AI_USAGE.md`: transparent AI usage documentation.
