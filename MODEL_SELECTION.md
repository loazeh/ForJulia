# Model selection

## Question
Predict customer churn to prioritize retention outreach. False negatives miss customers who may leave; false positives waste outreach and may annoy customers. This educational model is not validated for real customer decisions.

## Evaluation
All candidates use churn_v2.csv, the same stratified 80/20 split (seed 42), 1,200 training rows and 300 held-out rows, and a probability threshold greater than 0.5. Preprocessing is fitted on training data only. Latency is p95 of 200 single-row predict_proba calls inside local Docker, excluding HTTP transport. Size is joblib bytes divided by 1024 (KiB). Results are rounded to four decimals by MLflow.

| Candidate | Reason | AUC | F1 | Lowest slice F1 | p95 ms | Size KiB | MLflow run ID |
|---|---|---:|---:|---:|---:|---:|---|
| Logistic regression C=1 | Small linear baseline, reproducible and easy to serve | 0.7918 | 0.5868 | 0.1818 | 4.2639 | 3.5479 | 269ad7a6b7f3468b99e9b5e653013031 |
| Random forest, 150 trees, depth 6, leaf minimum 4 | Nonlinear interactions with constrained complexity | 0.7522 | 0.5325 | 0.0000 | 13.7991 | 1069.3457 | d8c54e3a7953490399f5ca35d8942989 |
| Gradient boosting, 120 trees, depth 2, rate 0.05 | Gradual nonlinear fitting with shallow trees | 0.7597 | 0.5357 | 0.2000 | 4.4959 | 100.3789 | 81f3eed9b72a400885adbd44ed30e948 |

## Contract slices
| Candidate | Month-to-month (191 rows) | One-year (60 rows) | Two-year (49 rows) |
|---|---:|---:|---:|
| Logistic regression | 0.6429 | 0.3750 | 0.1818 |
| Random forest | 0.5874 | 0.3529 | 0.0000 |
| Gradient boosting | 0.5775 | 0.3750 | 0.2000 |

## Champion and tradeoff
Choose logistic regression: it has the highest overall F1 (0.5868), highest AUC (0.7918), smallest artifact (3.5479 KiB), and lowest observed p95 (4.2639 ms). It beats boosting by 0.0511 absolute F1. I accept losing 0.0182 F1 on the two-year slice to boosting; this small slice contains only 49 held-out customers and all candidates perform poorly there. The choice follows the overall-F1 promotion policy, not a claim of uniformly better subgroup outcomes.

## Promotion rules
- p95 budget: 25 ms for single-row model inference, reserving roughly 75 ms of a provisional 100 ms request budget for transport, validation and queuing. This is a lab design target, not a measured production SLA. CI hardware can be slower; candidates must still pass the measured budget there.
- Minimum gain: 0.005 absolute F1 (half a percentage point) to avoid replacing the champion for negligible rounded differences. This threshold is operational, not a statistical significance test.
- Select the highest-F1 completed, logged candidate within budget. With no champion, bootstrap the first qualifying model. Otherwise reject a candidate below champion F1 plus the minimum gain. Failed or incomplete MLflow runs cannot be promoted.
- GitHub compares against champion.json on the PR base branch, not a proposed replacement baseline in the PR.

## Next checks
Repeat evaluation on untouched future data and use uncertainty intervals for the two-year slice. Comparing three models on this held-out split makes it a model-selection validation set; a separate final test set is needed before production. Confirm that monthly_fee and monthly_charges have the same units. Measure end-to-end API latency under load, not only single-row inference.

## Provenance
Source commit for final local runs: 5d5e0bb279fc6ad9ef51e679200e2865aafc5eb5.
Dataset SHA-256: 2b915d9a9afcfb66d9e13c119e4a7bc7b47dc0041af5c72dde6126e42a28570a.
MLflow experiment: churn; batch: lab3-final. Full parameters, signatures and model artifacts remain in the local MLflow volume. The starter's Lab3 helpers were adapted onto the working Lab2 repository.
