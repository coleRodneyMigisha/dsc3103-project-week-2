from pathlib import Path

from src.ingest.source_a import ingest_source_a
from src.ingest.source_b import ingest_source_b
from src.transform.clean import clean_data
from src.transform.merge import merge_data
from src.common.config import OUTPUT_PATH, SOURCE_A_RAW_PATH
from src.common.logging_setup import get_logger


logger = get_logger()

def run_pipeline():
    logger.info("=== Pipeline run started === \n")

    logger.info("Stage 1.0: Ingesting source A")
    source_a = ingest_source_a()
    logger.info(f"Stage 1.1: Source A ingested, Row count: {len(source_a)} \n")
    required_source_a = {"id", "date", "market", "commodity", "price"}
    missing = required_source_a - set(source_a.columns)

    if missing:
        raise ValueError(
            f"Source A schema error: missing columns {sorted(missing)}. \n"
            f"Expected columns: {sorted(required_source_a)}"
        )

    logger.info(f"Stage 2.0: Ingesting source B")
    source_b = ingest_source_b()
    logger.info(f"Stage 2.1: Source B ingested, Row count: {len(source_b)} \n")
    required_source_b = {"date", "market", "rainfall"}
    missing = required_source_b - set(source_b.columns)

    if missing:
        raise ValueError(
            f"Source B schema error: missing columns {sorted(missing)}. \n"
            f"Expected columns: {sorted(required_source_b)}"
        )


    logger.info(f"Stage 3.0: Cleaning source A")
    clean_prices, decisions = clean_data()
    logger.info(f"Stage 3.1: Source A cleaned \n"
                f"Rows in: {len(source_a)} \n"
                f"Rows out: {len(clean_prices)} \n")


    logger.info(f"Stage 4.0: Merging Price (source a) and Rainfall (source b) ")
    merged = merge_data(clean_prices, source_b)
    logger.info(f"Stage 4.1: Merge complete \n"
                f"Rows in: \n"
                f"  Source A -> {len(clean_prices)} \n"
                f"  Source B -> {len(source_b)} \n"
                f"Rows out: Merged -> {len(merged)} \n")


    logger.info(f"Stage 5.0: Saving merged file \n")
    output = Path(OUTPUT_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(output, index=False)
    logger.info(f"Stage 5.1: Saving {len(merged)} rows (merged file) to '{output}' \n")

    logger.info("=== PIPELINE RUN COMPLETED SUCCESSFULLY! ===")


if __name__ == "__main__":
    try:
        run_pipeline()
    except ValueError as exc:
        print(f"Pipeline rejected input: {exc}")
        raise SystemExit(2)