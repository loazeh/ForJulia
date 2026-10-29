"""Refactor of the Lab 1 churn notebook; run with python -m src.train.train."""

import json
from hashlib import sha256
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ["tenure_months", "monthly_charges", "contract", "internet_service", "support_calls"]


def train(data_path=ROOT / "data/churn_v2.csv", output_dir=ROOT / "artifacts"):
    data_path, output_dir = Path(data_path), Path(output_dir)
    df = pd.read_csv(data_path)
    if "monthly_fee" in df and "monthly_charges" not in df:
        df = df.rename(columns={"monthly_fee": "monthly_charges"})
    X_train, X_test, y_train, y_test = train_test_split(
        df[FEATURES], df["churn"], test_size=0.2, random_state=42, stratify=df["churn"]
    )
    model = Pipeline([
        ("prep", ColumnTransformer([
            ("num", StandardScaler(), ["tenure_months", "monthly_charges", "support_calls"]),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["contract", "internet_service"]),
        ])),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / "model.joblib"
    joblib.dump(model, artifact)
    metadata = {
        "dataset_sha256": sha256(data_path.read_bytes()).hexdigest(),
        "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
        "random_state": 42,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "features": FEATURES,
        "schema_mapping": "monthly_fee -> monthly_charges (Lab 1 v2 convention)",
        "f1": float(f1_score(y_test, probabilities > 0.5)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
    }
    (output_dir / "model.metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
