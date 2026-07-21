# AI Usage

I used OpenAI ChatGPT/Codex extensively to build this take-home assignment.

Codex generated the Python implementation, tests, documentation drafts, and repository cleanup changes through an interactive conversation. I directed the work, asked for step-by-step explanations, made product/design decisions, reviewed outputs, asked follow-up questions, and requested revisions when something was unclear, incomplete, or not submission-ready.

## What Codex Generated

- The project structure under `solution/`.
- The FastAPI mock API for internal merchant risk data.
- The API client that calls the mock API and validates responses against the provided JSON Schema contract.
- The REST Countries v5 integration, including bearer-token handling, fallback behavior, caching, and country-name normalization.
- The CSV ingestion and validation logic.
- The asynchronous PDF text extraction logic.
- The ClarityPay public-site scraper and multi-page crawl behavior.
- The collated underwriting view.
- Feature engineering for dispute-rate target creation, volume band, country region, internal risk flag, and registration-number presence.
- The logistic regression model and portfolio-level risk aggregation.
- The LLM report-generation flow, including prompt creation, credentialed generation, and no-key fallback behavior.
- Unit tests for ingestion, validation, scraping, features, model, portfolio aggregation, reporting, and submission shape.
- README and documentation files, including engineering decisions and written reports.

## Human Direction And Review

I provided the assignment requirements, asked Codex to work only inside the `solution/` folder, and required a structure matching the assignment brief.

I asked Codex to explain the project from first principles because much of the terminology was unfamiliar to me. I also asked for plain-English code comments/docstrings so I could understand and explain the implementation in an interview.

I made or confirmed key decisions, including:

- keeping the repository structure close to the assignment recommendation
- using FastAPI for the mock API
- treating the JSON Schema contract as the source of truth for the mock API response
- using REST Countries v5 after discovering the assignment's older REST Countries endpoint was deprecated
- skipping Companies House because it is optional and credential-dependent
- requiring honest fallback behavior when API keys are missing
- using a simple logistic regression model because the dataset is small
- moving private learning notes out of the public submission surface
- keeping generated outputs and secrets out of Git

## Representative Prompts And Instructions

This was an interactive conversation rather than one single prompt. Representative instructions I gave Codex included:

- "Implement Part 1 as a beginner-friendly simulated merchant risk API, explain what an API and endpoint are, and maintain a separate plan file."
- "Revise Part 2 to use REST Countries v5 because the original REST Countries endpoint in the assignment is deprecated, and document the obstacle."
- "Continue the remaining assignment step by step, create beginner-friendly plan files, add plain-English code comments, and document obstacles."
- "Convert the project from learning/demo shape into submission shape with one main pipeline command and professional documentation."
- "Create an honest AI usage document stating that Codex generated the implementation, tests, and documentation under my direction."
- "Use `gpt-5.6-terra` for the LLM underwriting report and keep API keys in `.env`, not in Git."
- "Remove private learning notes from the public repo and check the final submission against the assignment deliverables."

## Issues Found During The AI-Assisted Build

Several implementation details changed after inspection and testing:

- The assignment's mock API contract described one merchant object, while the example response showed a list. The final implementation uses a single-merchant endpoint to satisfy the contract.
- REST Countries legacy API versions were deprecated, so the integration was updated to v5.
- The REST Countries demo key returns example data only, so the code requires `RESTCOUNTRIES_API_KEY` for real enrichment.
- `Czech Republic` needed to be queried as `Czechia` for REST Countries enrichment while preserving the original CSV country name.
- `pdfplumber` extracted the sample PDF text in a noisy order, so the implementation prefers `pypdf` for this file and keeps `pdfplumber` as fallback.
- The initial ClarityPay scraper under-extracted public evidence. It was revised to extract client names, ecosystem partners, and only BNPL-underwriting-relevant public stats with source context.
- The first model feature encoding approach was revised to `DictVectorizer`, which better fits list-of-dictionary feature rows.
- A target-leakage risk was found in the initial model because dispute count and dispute rate helped define the target. The model was revised so those fields remain available for reporting and target creation but are excluded from model inputs.
- The LLM report prompt was revised to include model-framing context, including the target heuristic, target-leakage control, non-leaky model inputs, and small-data caveat.

## Verification

Codex ran the test suite repeatedly during development and revised the code when tests or manual checks exposed issues.

At the time this document was updated, the project test suite passed:

```text
43 tests passed
```

The full pipeline was also run locally with a real REST Countries API key set through an environment variable. That run enriched all merchant countries successfully. OpenAI report generation now reads `OPENAI_API_KEY` from the ignored local `.env` file and uses `gpt-5.6-terra` by default. When the pipeline is run with that key present, it generates the underwriting report locally under `outputs/`.

## Transparency Statement

This submission is AI-generated under my direction and review. I used the process to understand the assignment, inspect generated code, ask questions, and prepare to explain the design choices and tradeoffs live.
