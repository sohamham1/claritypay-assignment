# Engineering Decisions and Tradeoffs

This document records material implementation decisions, external-source limitations, and tradeoffs made while building the underwriting pipeline.

## API Contract Ambiguity

**Issue:** The assignment contract file describes one merchant response object, while the example response file shows a list of merchant objects.

**Why it matters:** Returning only a list would not directly satisfy the JSON Schema contract.

**Decision:** Use `GET /merchants/{merchant_id}` as the contract-satisfying endpoint that returns one merchant object.

**Result:** The mock API supports one-merchant responses that match the provided contract.

## REST Countries API Version Change

**Issue:** The assignment mentions REST Countries `/v3.1`, but current REST Countries documentation says legacy versions were taken down and `/v5` is the stable version.

**Why it matters:** Building against stale endpoints could break during a live walkthrough or review.

**Decision:** Use REST Countries v5 and document the difference from the original brief.

**Result:** The country enrichment client calls the v5 endpoint and uses bearer-token authentication.

## REST Countries Demo Key Limitation

**Issue:** The REST Countries v5 demo key returns example data rather than guaranteed real enrichment for the requested country.

**Why it matters:** Treating demo data as real merchant enrichment would be misleading.

**Decision:** Support `RESTCOUNTRIES_API_KEY` for real enrichment and return a clear fallback when only the demo key is available.

**Result:** A real key can enrich country code, region, and subregion; reviewers without a key still get honest fallback behavior.

## Country Name Normalization

**Issue:** The source CSV uses `Czech Republic`, while REST Countries v5 expects the common name `Czechia`.

**Why it matters:** Without a small alias, one valid merchant country falls back even when a real REST Countries key is configured.

**Decision:** Add a narrow country-name alias map for known source-data naming differences.

**Result:** The pipeline keeps the original merchant country text but queries REST Countries with the name it expects.

## CSV Validation

**Issue:** CSV files store values as text, even when a column looks numeric.

**Why it matters:** Risk calculations and model features need numeric values, not raw text strings.

**Decision:** Validate merchant rows with Pydantic and convert volume/count fields before downstream use.

**Result:** The pipeline uses typed, validated merchant records as its base table.

## Async PDF Processing

**Issue:** The assignment asks for asynchronous PDF processing, but a production queue would be unnecessary infrastructure for this take-home.

**Why it matters:** The solution should demonstrate async design without overbuilding.

**Decision:** Use an async wrapper around PDF extraction with `asyncio.to_thread`.

**Result:** The pipeline has an async PDF ingestion interface that could later be replaced by a queue-backed worker.

## PDF Extraction Quality

**Issue:** `pdfplumber` extracted text from the sample PDF, but the text order was jumbled.

**Why it matters:** Report context should be readable and inspectable.

**Decision:** Prefer `pypdf` for this sample and keep `pdfplumber` as a fallback extractor.

**Result:** The extracted PDF text is cleaner and more usable for collation/report context.

## Website Scraping Reliability

**Issue:** Public websites can change HTML structure, move content, or block requests.

**Why it matters:** Scraper failures should not crash the full underwriting pipeline.

**Decision:** Use a clear User-Agent, timeouts, page caps, small request delays, same-site public-link filtering, and fallback output.

**Result:** The scraper crawls multiple public ClarityPay pages respectfully and records failures without stopping the pipeline.

## Website Evidence Under-Extraction

**Issue:** The first scraper pass crawled multiple ClarityPay pages but under-extracted useful public evidence because it focused on visible text phrases and did not properly use logo alt text, newsroom copy, or context-aware statistic labels.

**Why it matters:** The assignment asks for partner/client names and public stats if available. At the same time, underwriting evidence must not treat random website numbers as risk facts.

**Decision:** Extract client names, ecosystem partners, and only BNPL-underwriting-relevant stats with labels, context, and source URLs. Exclude phone numbers, dates, addresses, form dropdown values, NMLS IDs, and other irrelevant numbers.

**Result:** The website context now carries structured client/partner names and sourced public stats that are useful for understanding ClarityPay's merchant financing ecosystem.

## Small Dataset Modeling Caveat

**Issue:** The dataset has only 50 merchants and no real historical underwriting outcome label.

**Why it matters:** A complex model would be misleading and hard to justify.

**Decision:** Use logistic regression with a transparent target derived from dispute count and dispute rate.

**Result:** The model is intentionally simple, explainable, and appropriate for the assignment scope.

## Model Feature Encoding

**Issue:** Plain Python feature dictionaries need to be converted into numeric model input.

**Why it matters:** Scikit-learn estimators require numeric arrays.

**Decision:** Use `DictVectorizer`, which is designed to convert list-of-dictionary feature rows into model-ready arrays.

**Result:** Numeric and categorical features are handled cleanly without adding pandas as a hard dependency.

## LLM Credential Handling

**Issue:** A ChatGPT subscription does not automatically provide OpenAI API access.

**Why it matters:** The assignment asks for an LLM-generated report, but generation requires API credentials.

**Decision:** Load `OPENAI_API_KEY` from the ignored local `.env` file or environment, generate the report when the key is present, and keep a clear prompt-only fallback for reviewers who run the project without credentials.

**Result:** The normal local run can generate the LLM underwriting report, while the report step remains auditable and honest in no-key environments.
