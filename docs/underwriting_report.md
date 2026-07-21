# BNPL Underwriting Risk Report

## Portfolio Overview

- **50 merchants** assessed.
- Model estimates **15.68 expected high-risk merchants**.
- **12 merchants** are currently assigned to the **high-risk band**.
- Simplified expected loss is **$17,210.20**, based on `predicted probability x monthly volume x 1% loss rate`.
- Sources were successfully processed: PDF extracted, website parsed, country enrichment completed, and internal-risk fields enriched.

## Website And Market Context

The ClarityPay scrape now includes structured public website evidence, not just homepage value propositions.

Extracted client/customer names include:

- LaserAway
- Safe Streets
- Club Wyndham
- Margaritaville Vacation Club
- JetBlue
- Diamonds International

Extracted ecosystem/funding/infrastructure partners include:

- DR Bank
- EXL
- Neuberger Berman
- Skeps
- TransUnion

Relevant public stats are stored with labels, context, and source URLs so they are not used as floating marketing numbers. Examples include:

| Label | Value | Underwriting context |
| --- | --- | --- |
| Approval coverage | 85% True Approvals | Merchant financing conversion context |
| Merchant conversion lift | 250% Increase in Conversion Rate | Merchant sales/conversion context |
| Average sale lift | 200% Higher Average Sale Amount | Merchant transaction economics context |
| Financing range | $50 to $50,000 | Consumer purchase/financing exposure range |
| Term range | 6 weeks to 84 months | Repayment-duration and product-risk context |
| Travel term range | 6 weeks to 48 months | JetBlue/travel financing context |
| Rollout footprint | more than 125 stores | Diamonds International merchant-scale context |
| Funding capacity | up to $1 billion | ClarityPay funding/capital purchase context |

These facts are useful for understanding ClarityPay's BNPL merchant ecosystem, but they are public website/newsroom claims. They should not be treated as independently validated merchant-level risk data.

## Key Merchant Risks

The highest-scored merchants are concentrated in Europe and include both merchants with existing high internal-risk flags and merchants whose model scores exceed their internal classifications.

| Merchant | Model probability | Internal flag | Monthly volume | Dispute rate | Key consideration |
| --- | ---: | --- | ---: | ---: | --- |
| M011 | 99.96% | High | $98,000 | 0.188% | Highest model score; high internal flag |
| M017 | 98.71% | High | $55,000 | 0.212% | High score with small-volume profile |
| M023 | 98.45% | High | $198,000 | 0.093% | High score and substantial monthly exposure |
| M002 | 96.80% | High | $89,000 | 0.238% | Highest dispute rate among listed merchants; Americas |
| M038 | 94.23% | Medium | $112,000 | 0.121% | Model/internal-risk mismatch |
| M028 | 93.05% | Medium | $142,000 | 0.098% | Model/internal-risk mismatch and material volume |
| M006 | 88.36% | Medium | $320,000 | 0.045% | Largest listed volume; high exposure despite low observed dispute rate |
| M027 | 84.82% | Medium | $73,000 | 0.122% | Model/internal-risk mismatch |
| M046 | 82.33% | Medium | $59,000 | 0.169% | Model/internal-risk mismatch |
| M041 | 81.62% | High | $51,000 | 0.203% | High internal flag and elevated dispute rate |

## Risk-Band Assessment

- The model places **12 of 50 merchants** in the high-risk band.
- The portfolio-level expected high-risk count is **15.68** because it sums all merchant risk probabilities, including probabilities below the high-band threshold.
- The top displayed high-risk scores range from **81.62% to 99.96%**.
- Five of the ten listed merchants, **M038, M028, M006, M027, and M046**, are classified as **medium** by internal risk while being assigned a **high model-risk band**. These cases warrant review of the drivers behind the model override.
- M006 is a priority exposure case: its dispute rate is comparatively low among the listed merchants, but its **$320,000 monthly volume** and **88.36% predicted risk probability** create significant potential loss exposure.

## Red Flags

1. **Internal/model classification divergence:** Five listed merchants have medium internal flags but high model-risk classifications.
2. **High-volume high-risk merchants:** M006 ($320,000), M023 ($198,000), M028 ($142,000), and M038 ($112,000) combine high predicted risk with meaningful monthly volume.
3. **Dispute-rate concentration:** M002 (0.238%), M017 (0.212%), and M041 (0.203%) have the highest dispute rates among the listed merchants.
4. **Regional concentration:** Nine of the ten listed top-risk merchants are in Europe; M002 is in the Americas.
5. **Risk not explained by dispute rate alone:** Several high-scored merchants have relatively low observed dispute rates, including M006 (0.045%) and M023 (0.093%). This suggests model outputs rely on factors beyond the provided dispute-rate field and should be reviewed for explainability.

## Model Performance And Production Caveats

- Reported model performance is **1.00 accuracy** and **1.00 ROC-AUC**. While strong, perfect results require validation before production use.
- The dataset size is limited to **50 merchants**. The data provided does not specify training/validation splits, out-of-sample testing, time-based validation, class balance, calibration, or leakage controls.
- Perfect metrics may reflect a limited or non-independent evaluation population; they should not be treated as proof of production performance without independent validation.
- The model probabilities should be assessed for **calibration**, particularly because risk-band decisions and expected-loss estimates directly depend on them.
- The expected-loss estimate uses a fixed **1% loss-rate assumption**. It is a simplified measure and does not demonstrate merchant-specific loss severity, recovery, timing, or changes in volume.
- The PDF excerpt is explicitly described as a **sample merchant terms and summary**. It should not be attributed to a specific portfolio merchant without verified entity linkage.
- Website context helps describe ClarityPay's market and product environment, but it should not be used as a direct merchant-level risk label unless linked to specific merchants and independently verified.

## Recommended Underwriting Posture

- Apply enhanced review to all **12 high-band merchants**, prioritizing high-score/high-volume merchants.
- Investigate model-versus-internal-flag discrepancies before relying solely on model classification.
- Validate model performance on an independent, time-separated sample and perform probability calibration testing.
- Treat the reported expected loss as a directional portfolio estimate pending confirmation of the fixed 1% loss-rate assumption and model calibration.
