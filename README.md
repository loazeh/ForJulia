# AI381 Lab 2 — Churn service

[![CI](https://github.com/loazeh/ForJulia/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/loazeh/ForJulia/actions/workflows/ci.yml)

From this repository directory, with Docker Desktop running, start the service with one command:

```powershell
docker compose up --build -d --wait
```

Open http://localhost:8000/docs for the interactive API. Stop with `docker compose down`.

## Try the API

```powershell
curl.exe http://localhost:8000/health
curl.exe -H "Content-Type: application/json" --data-binary "@sample_request.json" http://localhost:8000/predict
```

The sample returns `{"churn_probability":0.895}`. Health returns `status: ok` and the SHA-256 of the loaded model. A missing model prevents startup.

Inputs: nonnegative integer `tenure_months` and `support_calls`, finite nonnegative number `monthly_charges`, `contract` in `month-to-month / one-year / two-year`, and `internet_service` in `fiber / dsl / none`. Missing/extra fields and invalid values return HTTP 422.

## Train and test

Python 3.12 is used in CI and Docker. For native Python development:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m src.train.train
ruff check .
pytest -v
```

Or run the same checks locally inside Docker (no host Python needed):

```powershell
docker build --target test -t forjulia-tests .
docker run --rm forjulia-tests pytest -v
```

Tests protect the HTTP response contract, actual model loading, invalid input rejection, zero-valued boundaries, deterministic sample prediction, retraining reproducibility, and failure on missing model files.

## Model and data

This refactors the Lab 1 starter churn notebook into `src/train/train.py`. A StandardScaler and OneHotEncoder feed LogisticRegression. The stratified split is 80/20 with seed 42. `data/churn_v2.csv` is the supplied Lab 1 dataset; `monthly_fee` is mapped to `monthly_charges`, preserving the Lab 1 convention. No independent data dictionary was supplied to verify units. This is an educational model, not a validated customer decision system.

Training writes an artifact plus metadata with data/model hashes, held-out F1 and ROC-AUC, split sizes, and seed. The Docker build retrains using the same pinned libraries as runtime; no old pickle is copied from Lab 1.

## Container design

The base image is pinned by SHA-256 digest. The builder installs exact dependencies in `/opt/venv` and trains the model. The test target adds pytest and Ruff. The final runtime copies the environment, source, and model only; it runs as UID/GID 10001 and has an HTTP HEALTHCHECK. Compose binds to localhost, uses a read-only filesystem with `/tmp` in memory, drops capabilities, and prevents privilege escalation.

## CI and publication

Every pull request runs `lint-test`, then `build-scan-push` builds, scans, and smoke-tests the image. On main, those checks also publish `ghcr.io/loazeh/forjulia:<full-commit-SHA>`. The exact image digest appears in the build job summary and push log. Publication happens only after successful tests and scanning.

All directly referenced actions are pinned to full commit SHAs. Trivy blocks fixable HIGH/CRITICAL vulnerabilities; unfixed findings and lower severities are outside this gate. A green scan is not a claim that the image has no vulnerabilities. Main requires both checks and a pull request, including for administrators. Zero reviewer approvals are required because this is an individual lab.

## Recording and submission

Use `docs/recording-ar.md` for the Arabic 5–8 minute walkthrough. Upload the personally recorded video and `repo.txt` to the matching Teams assignment. The identity/profile, face, and voice must be Julia's own.
