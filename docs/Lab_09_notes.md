# DSC3103 — Lab 9 (Streaming and Event-Driven Data Systems) Notes

### Step 1 — Late and Duplicate Events in `producer.py`

**Two lines that deliberately create late events and duplicate events:**
- **Late events:** `delay = random.uniform(15, 40) if random.random() < 0.10 else 0` followed by `"event_time": now - delay` (10% of events are stamped with an `event_time` 15 to 40 seconds earlier than `now`).
- **Duplicate events:** `if random.random() < 0.05: log.write(line); log.flush()` (5% of events are written to the broker log a second time with the exact same `event_id`).

**Question:** Why does the producer sometimes make `event_time` earlier than the current time? Give an example of this scenario in the real-world.
- Because in real-world systems, the time an event actually occurred (`event_time`) is often earlier than the time the server receives it (`processing_time`) due to network delays or offline buffering.
- **Real-world example:** A market price clerk in a rural market (e.g. Gulu Main or Mbale Central) records a maize price on a mobile app at `10:00:05` while mobile network coverage is down; when the phone regains signal 30 seconds later, the event arrives at the broker at `10:00:35` with `event_time = 10:00:05`.

---

### Step 3 — Window Output Timing

**Question:** Does a window's result appear **immediately** after the window ends? Why not? What is the delay, and which constant controls it?
- No, a window's result does **not** appear immediately after the 10-second window ends.
- It waits because out-of-order (late) events belonging to that window might still be in transit.
- The delay after the window ends is **20 seconds** (so 30 seconds total after `window_start`, i.e. `now >= ws + WINDOW + WATERMARK`), and it is controlled by the `WATERMARK = 20` constant.

---

### Step 4 — Event Time vs Processing Time

**Question:** Using **your** output, if the window logic used the time the consumer **received** each event instead of `event_time`, which of your windows would have the wrong count, and why?
- In our run (`WATERMARK = 20`), **all 6 windows** had different counts under processing time vs event time:
  - `Window 1762379980`: event-time count = `3`, processing-time count = `0`
  - `Window 1762379990`: event-time count = `5`, processing-time count = `0`
  - `Window 1762380000`: event-time count = `79`, processing-time count = `83`
  - `Window 1762380010`: event-time count = `76`, processing-time count = `81`
  - `Window 1762380020`: event-time count = `72`, processing-time count = `80`
  - `Window 1762380030`: event-time count = `53`, processing-time count = `56`
- **Why:** Delayed events that actually happened in an earlier window (such as `1762379980` or `1762380000`) arrived 15–40 seconds later. Under processing time, they get falsely bucketed into whichever later window (`1762380000`–`1762380030`) happens to be open when they arrive, inflating the later windows and under-counting the earlier windows.

---

### Step 5 — Late Events and Watermark Trade-off

1. **With `WATERMARK = 20`:**
   - **Late events routed to `late_events.jsonl`:** `12` events (their delay exceeded `WINDOW + WATERMARK` so their window had already closed).
   - **Late events accepted into their correct window:** `13` delayed events arrived before `ws + 10 + 20` and were counted in their true event-time window.

2. **Watermark comparison table:**

| WATERMARK | Late events logged | Delay before a window prints |
|---|---|---|
| 5 | 25 | 5s after window end (15s after `ws`) |
| 20 | 12 | 20s after window end (30s after `ws`) |
| 40 | 0 | 40s after window end (50s after `ws`) |

**Question:** Which setting would you choose for a fraud alert, and which for a daily price report? Why?
- **For a fraud alert:** I would choose **`WATERMARK = 5`** (short watermark) because speed is critical — we need to flag suspicious activity within seconds before a fraudster cashes out, even if a few very delayed events have to be handled separately on a side output.
- **For a daily price report:** I would choose **`WATERMARK = 40`** (long watermark) because completeness and accuracy matter much more than a 40-second delay when computing official market price averages.

---

### Step 6 — Duplicates and State Growth

1. **How many duplicates were caught (`duplicate_events.jsonl`)?**
   - `11` duplicate events were caught and logged to `data/stream/duplicate_events.jsonl`.
2. **Comment out the code for duplicates and run again. How do the window counts change?**
   - The window counts increase by the duplicate events (`Window 1762380000` increases from `79` to `83`, `Window 1762380010` from `76` to `80`, `Window 1762380020` from `72` to `74`, and `Window 1762380030` from `53` to `54`), double-counting prices and distorting the window mean.
3. **`seen_ids` grows forever. For a stream of 10 million events a day, what would happen to it? Suggest one way to limit it, and say what risk your limit creates.**
   - **What would happen:** `seen_ids` is an in-memory Python `set`, so at 10 million IDs per day it would consume gigabytes of RAM and eventually crash the consumer with an Out-Of-Memory (`MemoryError`) failure.
   - **How to limit it:** Keep only `event_id`s from a bounded time-to-live (TTL) window (e.g. expire IDs older than `WINDOW + WATERMARK`, or store a fixed-size LRU / sliding time cache of the last 5 minutes).
   - **Risk created:** If a duplicate retry arrives *after* its `event_id` has expired from the cache, the consumer will not recognise it as a duplicate and will process it a second time (though if its `event_time` is old, the watermark check will still catch it as a late event).

---

### Step 7 — Stopping and Restarting the Consumer

1. **What happened to `offset`, `windows` and `seen_ids`?**
   - Because they were stored only in volatile RAM variables inside the Python process, stopping the consumer (`Ctrl+C`) wiped `offset` back to `0`, emptied `windows = {}`, and cleared `seen_ids = set()`.
2. **What does the restarted consumer do with events it had already counted?**
   - Since `offset` resets to `0`, the restarted consumer re-reads `data/stream/events.jsonl` from line 0 and re-processes all old events again (and because `now` is now much later than their `event_time`, it marks old finalised windows' events as late!).
3. **What would you have to save (checkpoint) so that a restart continues correctly?**
   - We must atomically checkpoint: (a) the file `offset` (line number read so far), (b) the open `windows` state (`n` and `total` per window start), (c) the `finalised` window set, and (d) the recent `seen_ids` set to durable disk/database storage.

---

### Step 8 — When is a 5-Minute Batch Job Enough vs Streaming?

- **When a 5-minute batch job is good enough:** For a public market-price dashboard or daily bulletin showing average commodity prices across Owino, Nakasero, and Mukono. Physical food prices in open-air markets change gradually over hours or days, so a 5-minute refresh has zero business downside and is much simpler to maintain.
- **When you need streaming:** When automated actions or alerts depend on immediate event detection — for example, detecting flash price manipulation/collusion in real time, triggering instant automated logistics bidding when supply drops at a market, or catching anomalous/fraudulent mobile-money commodity payments before settlement completes.


---


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
