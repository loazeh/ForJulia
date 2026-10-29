"""Validated FastAPI interface to the trained churn pipeline."""

import os
from contextlib import asynccontextmanager
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.train.train import FEATURES, ROOT


@asynccontextmanager
async def lifespan(app: FastAPI):
    path = Path(os.environ.get("MODEL_PATH", ROOT / "artifacts/model.joblib"))
    model_bytes = path.read_bytes()
    app.state.model = joblib.load(BytesIO(model_bytes))
    app.state.model_sha256 = sha256(model_bytes).hexdigest()
    yield


app = FastAPI(title="AI381 Lab 2 — Churn API", version="2.0.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Invalid numbers such as 1e999 become infinity in Python. Do not echo
    # those values into JSON errors, where they would cause a server error.
    errors = [{key: error[key] for key in ("type", "loc", "msg")} for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    tenure_months: int = Field(ge=0)
    monthly_charges: float = Field(ge=0)
    contract: Literal["month-to-month", "one-year", "two-year"]
    internet_service: Literal["fiber", "dsl", "none"]
    support_calls: int = Field(ge=0)


class Prediction(BaseModel):
    churn_probability: float = Field(ge=0, le=1)


@app.get("/health")
def health(request: Request):
    return {"status": "ok", "model_sha256": request.app.state.model_sha256}


@app.post("/predict", response_model=Prediction)
def predict(customer: Customer, request: Request):
    frame = pd.DataFrame([customer.model_dump()])[FEATURES]
    probability = float(request.app.state.model.predict_proba(frame)[0, 1])
    return Prediction(churn_probability=round(probability, 3))
