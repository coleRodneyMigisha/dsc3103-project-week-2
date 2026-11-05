# DSC3103 — Lab 9 Part 2 / Lab 10: From Model to Data Product (FastAPI + Docker) Notes

### Step 2 — Shared Feature Engineering (`src/common/features.py`)

**Question:** The training script and the API will both import `make_features`. What problem does this prevent? What would happen if the API had its own copy?
- Importing `make_features` from one shared module (`src/common/features.py`) prevents **training–serving skew** (where features are computed differently at inference time than during training).
- If the API had its own copy of the feature logic, a developer might later update one file (for example, changing how missing rainfall is imputed, adding a new market, or changing the one-hot column order) and forget to update the other. The API would then feed differently scaled or misaligned columns into the model and silently return wrong price predictions without crashing.

---

### Step 4 — Model Metadata (`models/model_metadata.json`)

Generated `models/model_metadata.json`:
```json
{
  "model_version": "20261106-003604",
  "model_type": "LinearRegression",
  "features": [
    "rainfall_mm",
    "month",
    "market_Owino",
    "market_Nakasero",
    "market_Kalerwe",
    "market_Mbale Central",
    "market_Gulu Main",
    "market_Unknown",
    "commodity_Maize",
    "commodity_Beans",
    "commodity_Cassava",
    "commodity_Rice"
  ],
  "n_training_rows": 889,
  "training_data_sha256": "e22dce4ca819e3075e15bc3b7a963c769f0bc137d2ab57c3036614d32538123d",
  "train_r2": 0.015
}
```

**Question:** Which fields would you use to answer: *"which data was this model trained on?"* and *"which model is serving right now?"*
- *"Which data was this model trained on?"*: **`training_data_sha256`** (the exact cryptographic SHA-256 hash of `prices_with_rainfall.parquet`) together with **`n_training_rows`** (`889`).
- *"Which model is serving right now?"*: **`model_version`** (`"20261106-003604"`) and **`model_type`** (`"LinearRegression"`), which are also exposed by `GET /health` and returned in every `POST /predict` response.

---

### Step 7 — Request Validation Results

| Request | Status | Message |
|---|---|---|
| `rainfall_mm` = -5 | `422 Unprocessable Entity` | `Input should be greater than or equal to 0` |
| `market` = "Narnia" | `422 Unprocessable Entity` | `Input should be 'Owino', 'Nakasero', 'Kalerwe', 'Mbale Central', 'Gulu Main' or 'Unknown'` |
| `date` = "not-a-date" | `422 Unprocessable Entity` | `Input should be a valid date or datetime, invalid character in year` |

**Question:** Why is a 422 better than a 500, or than returning a prediction anyway?
- **Why 422 is better than 500:** HTTP `422` tells the caller immediately that *their request payload* violated the API contract and names the exact field (`rainfall_mm`, `market`, or `date`) so they can fix it, whereas HTTP `500` means our server crashed and triggers false production outage alerts.
- **Why 422 is better than returning a prediction anyway:** A linear model will happily multiply `rainfall_mm = -5` by its learned weight or treat `"Narnia"` as all-zeros in the market one-hot columns and return a confident-looking garbage price. Rejecting bad inputs at the boundary stops garbage-in, garbage-out.

---

### Step 8 — Breaking It on Purpose: Training–Serving Skew

1. **Valid request before change (`{"market": "Owino", "commodity": "Maize", "date": "2026-03-15", "rainfall_mm": 4.2}`):**
   - Returned `HTTP 200`: `{"predicted_price": 2927.25, "model_version": "20261106-003604"}`.
2. **After changing `out["rainfall_mm"] = df["rainfall_mm"].fillna(0.0) / 1000` in `features.py` without retraining:**
   - Returned `HTTP 200`: `{"predicted_price": 2889.58, "model_version": "20261106-003604"}`.

**Questions:** Did the service crash? Did the prediction change? What does this tell you about why `/health` should report the model version, and what additional field could you add to the metadata to detect a feature-code change?
- **Did the service crash?** No — it returned `HTTP 200 OK` without any error or warning.
- **Did the prediction change?** Yes — the predicted price silently dropped from **`2927.25`** to **`2889.58`** (a difference of `37.67` UGX) because the model multiplied a `1000x` smaller rainfall number by the original weight trained on millimetres.
- **What this tells us:** Reporting `model_version` in `/health` confirms which model artifact is loaded, but it cannot by itself catch a change made to `features.py` after training. To detect a feature-code change automatically, we should add **`features_code_sha256`** (the SHA-256 hash of `src/common/features.py` at training time) to `model_metadata.json` and verify at API startup (and in `/health`) that the current `features.py` hash matches the hash recorded when the model was trained.

---

### Step 10 — Containers and Pinned Dependencies

**Question:** Why must the scikit-learn version in the image match the one that trained the model? Why is `data/` left out of the image?
- **Why `scikit-learn` version must match:** `joblib` serialises the internal Python object structure of the `LinearRegression` estimator. Different versions of `scikit-learn` can change internal attribute names, array layouts, or numerical routines, causing `joblib.load()` in the container to fail with an `AttributeError`/`ValueError` or produce subtly different predictions.
- **Why `data/` is left out of the image (`.dockerignore`):** The inference service only needs the trained `models/model.joblib` artifact and `models/model_metadata.json` to serve predictions. Excluding `data/` (which contains multi-megabyte raw CSVs and 5M-row Parquet files) keeps the Docker image small, fast to build and deploy, and avoids shipping raw/historical datasets inside a public container.
- *(Note: Step 11 reproducibility verification was executed using the `uvicorn` process directly.)*

---

### Step 11 — Reproducibility Verification (`uvicorn` Restart)

**Call 1 (Before restart):**
```
--- health: HTTP 200
{'status': 'ok', 'model_version': '20261106-003604', 'model_type': 'LinearRegression'}
--- valid predict: HTTP 200
{'predicted_price': 2927.25, 'model_version': '20261106-003604'}
```

**Call 2 (After stopping and restarting `uvicorn`):**
```
--- health: HTTP 200
{'status': 'ok', 'model_version': '20261106-003604', 'model_type': 'LinearRegression'}
--- valid predict: HTTP 200
{'predicted_price': 2927.25, 'model_version': '20261106-003604'}
```

**Observation:**
- Both calls before and after restarting the service return the **exact same price (`2927.25`)** and **`model_version` (`20261106-003604`)**. Because the model is trained offline once, saved to disk (`models/model.joblib`), and loaded deterministically at startup rather than retrained on the fly, restarts always produce identical predictions for identical inputs.

---

### Step 12 — Summary Questions

1. **Where does preprocessing happen at inference time?**
   - Inside the `POST /predict` endpoint in `src/api/main.py`: after Pydantic validates the incoming `PriceRequest`, the endpoint constructs a 1-row DataFrame, passes it through `make_features(df)` imported from `src/common/features.py`, and orders the columns with `X = X[metadata["features"]]` right before calling `model.predict(X)`.

2. **How does your design prevent training–serving skew? Which Step showed it can still happen and how?**
   - It prevents skew by writing feature engineering once in `src/common/features.py` (`make_features`) and importing that exact function in both `src/ml/train.py` and `src/api/main.py`, plus enforcing the exact column order via `X[metadata["features"]]`.
   - **Step 8** showed skew can still happen if someone edits `src/common/features.py` (dividing `rainfall_mm` by 1000) *after* the model was trained and restarts the API without retraining `model.joblib`.

3. **What should `/health` prove?**
   - `/health` should prove not just that the HTTP web server process is alive (`"status": "ok"`), but that the model artifact and metadata are loaded and ready to serve, reporting `"model_version"` and `"model_type"` so callers and monitoring tools know *which* model is currently serving.

4. **Which information belongs with a model version, and why?**
   - `model_version` (timestamp/ID) to identify the active model and support rollbacks; `model_type` to know the algorithm; `features` (exact list and order of input columns) to enforce the input contract; `training_data_sha256` and `n_training_rows` to trace exactly which dataset produced the model; `train_r2` (evaluation metric) to know its baseline quality; and pinned library versions (`requirements.txt`).

5. **When would batch inference be a better choice than this API for market prices?**
   - When we need to generate a scheduled nightly or weekly forecast table for **all** markets and commodities at once (e.g. pre-computing next week's expected prices for 50 markets to load into DuckDB or a morning report). Running one scheduled batch job over a DataFrame is simpler, cheaper, and higher-throughput than making thousands of individual HTTP calls, whereas the FastAPI service is better when a farmer or mobile app asks for a single prediction on demand.
