# Lab 3 implementation

Extends the working Lab 2 service using the supplied Lab 3 additions, as instructed. Local Docker Compose deployment implements Option B.

Three measured candidates, the selected model, contract slices and limitations are documented in MODEL_SELECTION.md. MLflow stores their parameters, dataset hash, signatures and models. The champion is registered as churn-model@champion and exported under artifacts/.

The pull-request gate compares candidates to the base branch champion with a 25 ms p95 budget and a minimum F1 gain of 0.005. The deliberately worse-model pull request must remain unmerged. The local deployment packages the exported champion and exposes commit and run lineage through /health.
