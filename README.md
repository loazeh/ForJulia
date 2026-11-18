# AI381 Lab 3 — Tracked, Gated and Shipped

[![CI](https://github.com/loazeh/ForJulia/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/loazeh/ForJulia/actions/workflows/ci.yml)

This extends the working Lab2 churn API with instructor-provided Lab3 MLflow helpers. Three candidates are compared in [MODEL_SELECTION.md](MODEL_SELECTION.md). Logistic regression is the selected champion. Deployment uses Option B: local Docker Compose.

## Start the champion (PowerShell)

With Docker Desktop running, from this repository:

```powershell
$env:GIT_SHA = git rev-parse HEAD; docker compose -f docker-compose.deploy.yml up --build -d --wait
```

Service: http://localhost:8000/docs. Health: http://localhost:8000/health.

```powershell
curl.exe http://localhost:8000/health
curl.exe -H "Content-Type: application/json" --data-binary "@sample_request.json" http://localhost:8000/predict
```

The deployment image packages the exported champion; it does not train a replacement. It runs as UID 10001 with a health check. Compose binds to localhost and uses restart: unless-stopped, a read-only filesystem, a temporary /tmp, dropped capabilities, and no privilege escalation.

## MLflow and training

```powershell
docker compose -f docker-compose.mlflow.yml up -d --wait
docker build -f Dockerfile.training -t forjulia-lab3-training .
$sha = git rev-parse HEAD
docker run --rm -v "${PWD}:/work" -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 -e BATCH=new-candidates -e GIT_SHA=$sha forjulia-lab3-training python -m src.train.train_mlflow
```

Open http://localhost:5000, experiment churn. The final measured local comparison is batch lab3-final. Runs log settings, full dataset SHA-256, overall/slice metrics and counts, p95 single-row latency, size, signature, model, and training commit. Models > churn-model exposes the champion alias. Local MLflow state persists in the mlflow-data Docker volume. A new machine must train/register its own runs; GitHub's ephemeral runner MLflow state is not a remote tracking service.

## Promotion and tests

```powershell
docker run --rm -v "${PWD}:/work" -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 -e BATCH=new-candidates -e GIT_SHA=$sha forjulia-lab3-training python scripts/promote.py
docker run --rm -v "${PWD}:/work" forjulia-lab3-training pytest -q
docker run --rm -v "${PWD}:/work" forjulia-lab3-training python scripts/smoke_test.py http://host.docker.internal:8000
```

The gate selects completed, logged candidates within a 25 ms inference budget, then requires at least 0.005 absolute F1 improvement over the existing champion. Equal performance is BLOCKED. The first qualifying model bootstraps an empty registry. In CI, the baseline comes from the PR base commit. A deliberately worse model must stay on an unmerged PR.

The train-and-gate workflow builds and smoke-tests its promoted model. The inherited CI workflow separately verifies the Lab2 baseline service and publishes that baseline image; the Lab3 champion is deployed with Dockerfile.deploy and docker-compose.deploy.yml, not that baseline image.

## Lineage

The local image tag and health model_version are the deployment commit. That commit contains artifacts/metadata.json with the MLflow run ID. The run's git_sha is the earlier training-source commit, and its data_sha256 identifies the exact data bytes. Training and deployment commits can differ because the artifact is exported after training. The model hash in health identifies the bytes actually loaded.

## Stop

```powershell
docker compose -f docker-compose.deploy.yml down
docker compose -f docker-compose.mlflow.yml down
```

Do not use down -v if you want to retain experiment history. Pickle/joblib artifacts must only be loaded from trusted sources. The supplied dataset is educational; the weak two-year slice requires further evaluation before real use.
