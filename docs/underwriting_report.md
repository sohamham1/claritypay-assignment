# BNPL Underwriting Risk Report

## Portfolio Overview

- Merchants assessed: **50**
- Model-expected high-risk merchants: **15.83**
- Model high-risk band: **5 merchants**
- Simple expected monthly loss: **$17,159.13**, calculated as `predicted probability x monthly volume x 1% assumed loss rate`
- Data sources processed: PDF extracted, website parsed, country enrichment completed, and internal-risk data enriched.

The expected high-risk count is a probability-summed portfolio estimate. It can be decimal because it adds every merchant's predicted probability. The high-risk-band count is a hard count of merchants whose probability crossed the high-band threshold.

## Model Framing And Reliability

The model predicts a derived assignment label:

```text
high dispute risk = dispute_count >= 3 OR dispute_rate >= 0.0015
```

This target is a transparent assignment heuristic because no real historical underwriting outcome label was supplied.

Latest model metrics:

- Accuracy: **69.2%**
- ROC-AUC: **83.3%**

The model has a specific target-leakage control: `dispute_count` and `dispute_rate` are used only to create and report the target, and are excluded from model input features. Inputs are monthly volume, transaction count, volume band, country region, internal-risk flag, and registration-number availability.

Metrics should be treated as directional only, not production-ready validation. The dataset is small and the target is derived, so predicted probabilities and risk bands should support manual underwriting prioritization rather than automated approval, decline, pricing, or limit decisions.

## Highest-Risk Merchants

| Merchant | Risk band / probability | Key risk indicators |
| --- | ---: | --- |
| M011 | High / 91.6% | 6 disputes; 0.188% dispute rate; high internal-risk flag; no registration number; $98k monthly volume |
| M017 | High / 80.0% | 4 disputes; 0.212% dispute rate; high internal-risk flag; $55k monthly volume |
| M006 | High / 79.7% | $320k monthly volume and 8,900 transactions; 4 disputes; medium internal-risk flag |
| M023 | High / 69.2% | $198k monthly volume; 5 disputes; high internal-risk flag |
| M005 | High / 68.3% | 3 disputes; 0.250% dispute rate; high internal-risk flag; no registration number |

M006 and M023 are important exposure cases because they combine high-band model classification with larger monthly volumes.

## Medium-Risk Merchants Requiring Review

- M027: 61.9% probability; 3 disputes; medium internal-risk flag; $73k monthly volume
- M028: 61.1% probability; 4 disputes; no registration number; $142k monthly volume
- M041: 60.5% probability; 3 disputes; 0.203% dispute rate; high internal-risk flag; no registration number
- M050: 58.3% probability; not currently assigned the heuristic target, but has medium internal-risk flag and $145k monthly volume
- M047: 53.6% probability; not currently assigned the heuristic target, but has medium internal-risk status, no registration number, and $97k monthly volume

M050 and M047 are notable model-alert cases because they are outside the current derived target definition but receive medium predicted-risk scores. These cases warrant manual review rather than being treated as confirmed high-risk merchants.

## Public Website Context

The ClarityPay scrape extracted public BNPL context, not merchant-specific performance proof.

Client names found in public context include LaserAway, Safe Streets, Club Wyndham, Margaritaville Vacation Club, JetBlue, and Diamonds International.

Ecosystem partner names found in public context include DR Bank, EXL, Neuberger Berman, Skeps, and TransUnion.

Relevant public stats were retained only with context and source URLs. Examples include approval coverage, merchant conversion lift, average sale lift, financing ranges, term ranges, store rollout footprint, transaction scale, and funding capacity. These are useful for understanding ClarityPay's merchant-financing ecosystem, but they are not treated as independently verified underwriting facts.

## Key Red Flags

1. High internal-risk flags: M011, M017, M023, M005, and M041.
2. Missing registration numbers: M011, M005, M028, M041, and M047.
3. Observed dispute activity: the highest-risk cases have 3 to 6 disputes.
4. High exposure combined with dispute counts: M006 and M023 present potentially material exposure despite dispute rates below 0.15%, because the heuristic triggers on either dispute count or rate.
5. Elevated model scores without current target assignment: M050 and M047 require monitoring and review for emerging risk.

## Recommended Underwriting Posture

Place the five high-band merchants into enhanced review, with priority to M011, M017, M006, M023, and M005. Verify registration and legal-entity details for merchants without a registration number, especially where missing registration combines with high internal-risk flags or elevated dispute activity.

Review dispute drivers, transaction and fulfillment controls, customer disclosures, refund practices, and relevant terms for merchants with three or more disputes. Monitor medium-band merchants, particularly M050 and M047, as potential early-warning cases.

## Production Caveats

This output should not be used as a standalone production underwriting decision engine. The small sample, heuristic-derived target, and directional model metrics limit confidence in probability calibration and generalization. The target-leakage control appropriately excludes dispute count and dispute rate from model features, but this does not remove the need for independent out-of-sample validation, stability testing, threshold governance, and ongoing performance monitoring before deployment.
