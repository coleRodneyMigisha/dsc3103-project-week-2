import os
import time
import pandas as pd
import duckdb as db

RAW_JOINED_PATH = "data/processed/prices_with_rainfall.parquet"

def baseline_query():
    t0 = time.perf_counter()
    result = db.sql(f"""
        SELECT market, AVG(price) AS mean_price
        FROM '{RAW_JOINED_PATH}'
        WHERE commodity = 'Maize'
        GROUP BY market
        ORDER BY mean_price DESC
    """).df()
    elapsed = time.perf_counter() - t0
    print("=== Step 1: Baseline query (flat Parquet) ===")
    print(result)
    print(f"Time: {elapsed:.4f}s | File size: {os.path.getsize(RAW_JOINED_PATH)} bytes")
    return elapsed



if __name__ == "__main__":
    baseline_query()
    # TODO