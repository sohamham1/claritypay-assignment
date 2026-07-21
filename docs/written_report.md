# Short Written Report

## Summary

This project implements a minimal production-style merchant underwriting pipeline for a BNPL setting.

The pipeline ingests five required data sources, validates and collates them into one merchant-level underwriting view, builds risk features, trains an explainable model, aggregates portfolio risk, and prepares an LLM underwriting report from pipeline outputs.

## BNPL Risk Framing

The underwriting problem is not only whether a merchant is risky, but whether that risk is understood and priced.

The core risks considered here are:

- dispute risk: merchants may create customer harm that leads to disputes or chargebacks
- merchant responsibility: the sample PDF states merchants are responsible for fraud and service disputes
- counterparty/portfolio risk: individual merchant risk needs to be aggregated into a portfolio-level view

The model and portfolio summary are intentionally simple, but they connect merchant-level signals to expected portfolio exposure.

## Assumptions

- `merchants.csv` is the base merchant population.
- The mock API represents an internal merchant risk service.
- REST Countries v5 is used because older REST Countries versions are deprecated.
- Real REST Countries enrichment is available when `RESTCOUNTRIES_API_KEY` is configured.
- Companies House is skipped because it is optional and requires credentials.
- The PDF is processed with an async wrapper as a lightweight stand-in for a production background job.
- The model target is derived from dispute count and dispute rate because no real historical underwriting outcome label is provided.
- Dispute count and dispute rate are kept for reporting and target creation, but excluded from model inputs to avoid target leakage.
- Model input features are monthly volume, transaction count, volume band, country region, internal risk flag, and registration-number presence.
- OpenAI report generation uses `gpt-5.6-terra` by default and reads `OPENAI_API_KEY` from the local `.env` file or environment. With the key configured, the pipeline generates the underwriting report locally under `outputs/`.

## Tradeoffs

- The model is simple by design. Logistic regression is easier to explain and more appropriate for a small dataset than a complex model.
- The model avoids target leakage by not training on the same dispute fields used to define the target label.
- The LLM report prompt includes the target heuristic, target-leakage control, non-leaky model inputs, and small-data caveat so the generated report reflects the model governance choices.
- The ClarityPay scraper crawls public site and newsroom pages, but parsing is conservative because public website HTML can change.
- Public stats are extracted only when they are relevant to BNPL merchant underwriting and can be stored with context, such as approval coverage, merchant conversion impact, financing range, rollout footprint, or funding capacity.
- Source fallback/status fields are preserved instead of hidden so downstream users can see when enrichment was unavailable.
- Generated outputs are written locally under `outputs/` and are not committed by default.

## Governance Coverage

- **Schema validation:** CSV rows are validated with Pydantic. Mock API responses are validated against the provided JSON Schema contract.
- **Source status fields:** Collated rows preserve source statuses such as country enrichment status, PDF extraction status, website scrape status, and internal risk status.
- **Idempotency approach:** In production, each run would have a run ID, deterministic output locations, and persisted source snapshots so reruns are auditable and do not create confusing duplicates.
- **Logging:** The command-line pipeline logs key stages and source fallback warnings. Production hardening would replace this with structured logs, run IDs, and centralized monitoring.
- **Tests:** Unit tests cover CSV validation, API response validation, REST Countries parsing/fallbacks, PDF extraction, website scraping, feature creation, model training, portfolio aggregation, and both LLM prompt fallback behavior and credential-ready report generation flow.
- **API key handling:** REST Countries and OpenAI keys are read from `.env` or environment variables and are not committed to the repository.
- **Generated artifacts:** `outputs/` is ignored by Git so generated JSON, prompts, and reports remain local unless intentionally copied into docs.

## Production Improvements

- Replace the mock API with a real internal underwriting/risk service.
- Add durable orchestration, retries, structured logging, and monitoring.
- Use a real queue or background worker for PDF processing.
- Store API credentials in a secret manager.
- Store intermediate datasets with run IDs for idempotency and auditability.
- Monitor model drift and retrain on real underwriting/dispute outcomes.
- Add stronger source data contracts and service-level expectations for upstream systems.
