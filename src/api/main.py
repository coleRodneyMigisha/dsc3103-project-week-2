import json
from datetime import date
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.common.features import make_features

MODEL_PATH = "models/model.joblib"
META_PATH = "models/model_metadata.json"

app = FastAPI(title="Market Price Prediction Service")

model = joblib.load(MODEL_PATH)
with open(META_PATH) as f:
    metadata = json.load(f)


# TODO 1 (validation): this request accepts ANY text and ANY number.
#   - "market" must be one of the six known markets
#   - "commodity" must be one of the four known commodities
#   - "date" must be a real date
#   - "rainfall_mm" must be between 0 and 500
#   Hint: use typing.Literal, datetime.date, and pydantic.Field(ge=..., le=...)
class PriceRequest(BaseModel):
    market: Literal["Owino", "Nakasero", "Kalerwe", "Mbale Central", "Gulu Main", "Unknown"]
    commodity: Literal["Maize", "Beans", "Cassava", "Rice"]
    date: date
    rainfall_mm: float = Field(ge=0, le=500)


# TODO 2 (health): report more than "ok". Include model_version and
#   model_type from the metadata, so a caller can tell WHICH model is serving.
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_version": metadata["model_version"],
        "model_type": metadata["model_type"],
    }


# TODO 3 (features): this calls the model on raw values. Instead:
#   a) build a one-row DataFrame from the request fields,
#   b) pass it through make_features() from src.common.features,
#   c) reorder columns with  X = X[metadata["features"]]
#   d) predict, and return predicted_price (rounded) and model_version.
@app.post("/predict")
def predict(r: PriceRequest):
    df = pd.DataFrame([{
        "market": r.market,
        "commodity": r.commodity,
        "date": str(r.date),
        "rainfall_mm": r.rainfall_mm,
    }])
    X = make_features(df)
    X = X[metadata["features"]]
    pred = float(model.predict(X)[0])
    return {
        "predicted_price": round(pred, 2),
        "model_version": metadata["model_version"],
    }
