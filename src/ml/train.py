import hashlib
import json
import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.common.features import make_features

DATA_PATH = "data/processed/prices_with_rainfall.parquet"
MODEL_PATH = "models/model.joblib"
META_PATH = "models/model_metadata.json"


def file_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def train():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    df = pd.read_parquet(DATA_PATH).dropna(subset=["price"])
    X = make_features(df)
    y = df["price"]

    model = LinearRegression().fit(X, y)
    joblib.dump(model, MODEL_PATH)

    metadata = {
        "model_version": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "model_type": "LinearRegression",
        "features": list(X.columns),
        "n_training_rows": len(df),
        "training_data_sha256": file_sha256(DATA_PATH),
        "train_r2": round(model.score(X, y), 4),
    }
    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print("Saved", MODEL_PATH, "and", META_PATH)
    print(metadata["model_version"], "R2 =", metadata["train_r2"])


if __name__ == "__main__":
    train()
