# Lab 05 Notes — Workflow Automation and Orchestration

**Step 3 — Configure retries, deliberately, per task**
- `acquire_a` and `acquire_b`: `retries=3, retry_delay=timedelta(minutes=2)` because ingestion depends on external files or API calls (like Open-Meteo rainfall API) which can fail temporarily due to network timeouts or transient I/O errors.
- `clean`, `merge`, and `store`: `retries=1, retry_delay=timedelta(minutes=1)` because these are deterministic local transformations and DuckDB writes; if a lock or temporary disk issue occurs, one retry helps, otherwise a data/schema bug needs manual inspection rather than endless retries.
- `report`: `retries=0` because it only reads the already-built DuckDB table to report the final row count.

**Step 5 & 6 — Failure injection and recovery**
- When `data/raw/rain.csv` was renamed (or its `rainfall` column was changed to `precipitation`), the `acquire_b` / `merge` task failed immediately in Airflow and the downstream `store` and `report` tasks were marked `upstream_failed`.
- From the Airflow task log alone, it was clear which stage failed and why (missing file or schema error on column `rainfall`).
- After restoring the file/schema and re-triggering the DAG, all tasks (`acquire_a`, `acquire_b`, `clean`, `merge`, `store`, `report`) reached `success`.
