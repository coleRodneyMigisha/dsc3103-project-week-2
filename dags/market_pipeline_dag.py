from airflow.sdk import DAG, task
from datetime import datetime, timedelta
import pandas as pd

from src.ingest.source_a import ingest_source_a
from src.common.config import SOURCE_A_RAW_PATH, SOURCE_B_RAW_PATH
from src.ingest.source_b import ingest_source_b
from src.transform.clean import clean_data
from src.transform.merge import merge_data
from src.analytics.build_analytics import build_star_schema
from src.analytics.build_analytics import DB_PATH

import duckdb

CLEAN_OUTPUT_PATH = "data/processed/prices_clean_dag.parquet"
JOINED_OUTPUT_PATH = "data/processed/prices_with_rainfall.parquet"


with DAG(
    dag_id = 'market_pipeline',
    schedule = '@daily',
    start_date=datetime(2026, 10, 1),
    catchup = False
):
    @task(retries=3, retry_delay=timedelta(minutes=2))
    def acquire_a():
        df = ingest_source_a(SOURCE_A_RAW_PATH)

        return {
            "path" : SOURCE_A_RAW_PATH,
            "rows" : len(df)
        }

    @task(retries=3, retry_delay=timedelta(minutes=2))
    def acquire_b():
        df = ingest_source_b(SOURCE_B_RAW_PATH)

        return {
            "path" : SOURCE_B_RAW_PATH,
            "rows" : len(df)
        }

    @task(retries=1, retry_delay=timedelta(minutes=1))
    def clean(acquire_a_result: dict):
        clean_df, log = clean_data(acquire_a_result['path'])
        clean_df.to_parquet(CLEAN_OUTPUT_PATH, index=False)
        return {
            'path' : CLEAN_OUTPUT_PATH,
            'rows' : len(clean_df),
            'rules_triggered' : len(log)
        }

    @task(retries=1, retry_delay=timedelta(minutes=1))
    def merge(cleaned: dict, acquire_b_result: dict):
        cleaned_data = pd.read_parquet(cleaned['path'])
        b_df = pd.read_csv(acquire_b_result['path'])
        merged_df = merge_data(cleaned_data, b_df)
        merged_df.to_parquet(JOINED_OUTPUT_PATH, index=False)
        return {
            'path' : JOINED_OUTPUT_PATH,
            'rows' : len(merged_df)
        }

    @task(retries=1, retry_delay=timedelta(minutes=1))
    def store(merged: dict):
        build_star_schema()
        return {
            'status' : 'Star Schema built successfully'
        }

    @task(retries=0)
    def report():
        con = duckdb.connect(DB_PATH)
        row_count = con.sql(
            "SELECT COUNT(*) FROM fact_price_observation"
        ).fetchone()[0]
        con.close()
        return {
            "run_date": "{{ ds }}",
            "fact_table_row_count": row_count
        }


    a = acquire_a()
    b = acquire_b()
    cleaned = clean(a)
    merged = merge(cleaned, b)
    stored = store(merged)
    report_gen = report()
    stored >> report_gen
