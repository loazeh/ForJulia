import json
from hashlib import sha256

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.train.train import ROOT, train


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    train()


@pytest.fixture
def client():
    with TestClient(app) as session:
        yield session


@pytest.fixture
def customer():
    return json.loads((ROOT / "sample_request.json").read_text())


def test_health_proves_model_loaded(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_sha256": sha256((ROOT / "artifacts/model.joblib").read_bytes()).hexdigest(),
    }


def test_prediction_contract(client, customer):
    response = client.post("/predict", json=customer)
    assert response.status_code == 200
    assert set(response.json()) == {"churn_probability"}
    assert 0 <= response.json()["churn_probability"] <= 1


@pytest.mark.parametrize("field,value", [
    ("tenure_months", -1), ("monthly_charges", -0.01), ("support_calls", -1),
    ("tenure_months", "5"), ("support_calls", True),
    ("contract", "unknown"), ("internet_service", "satellite"),
    ("extra_field", 123), ("monthly_charges", None),
])
def test_invalid_schema_rejected(client, customer, field, value):
    customer[field] = value
    assert client.post("/predict", json=customer).status_code == 422


def test_missing_field_rejected(client, customer):
    del customer["contract"]
    assert client.post("/predict", json=customer).status_code == 422


def test_nonfinite_rejected(client, customer):
    payload = json.dumps(customer).replace('89.9', '1e999')
    assert client.post("/predict", content=payload, headers={"Content-Type": "application/json"}).status_code == 422


def test_zero_boundary(client, customer):
    customer.update(tenure_months=0, monthly_charges=0.0, support_calls=0)
    response = client.post("/predict", json=customer)
    assert response.status_code == 200
    assert 0 <= response.json()["churn_probability"] <= 1


def test_deterministic_known_prediction(client, customer):
    for _ in range(3):
        assert client.post("/predict", json=customer).json() == {"churn_probability": 0.895}


def test_retraining_reproduces_predictions(tmp_path, customer):
    train(output_dir=tmp_path)
    original = joblib.load(ROOT / "artifacts/model.joblib")
    rebuilt = joblib.load(tmp_path / "model.joblib")
    frame = pd.DataFrame([customer])
    assert original.predict_proba(frame) == pytest.approx(rebuilt.predict_proba(frame), abs=1e-12)


def test_missing_model_fails_startup(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing.joblib"))
    with pytest.raises(FileNotFoundError), TestClient(app):
        pass
