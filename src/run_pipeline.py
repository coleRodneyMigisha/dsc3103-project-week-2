from pathlib import Path

from src.ingest.source_a import ingest_source_a
from src.ingest.source_b import ingest_source_b
from src.transform.clean import clean_data
from src.transform.merge import merge_data
from src.common.config import OUTPUT_PATH, SOURCE_A_RAW_PATH


def run_pipeline():
    source_a = ingest_source_a()
    required_source_a = {"id", "date", "market", "commodity", "price"}
    missing = required_source_a - set(source_a.columns)

    if missing:
        raise ValueError(
            f"Source A schema error: missing columns {sorted(missing)}. \n"
            f"Expected columns: {sorted(required_source_a)}"
        )

    source_b = ingest_source_b()
    required_source_b = {"date", "market", "rainfall"}
    missing = required_source_b - set(source_b.columns)

    if missing:
        raise ValueError(
            f"Source B schema error: missing columns {sorted(missing)}. \n"
            f"Expected columns: {sorted(required_source_b)}"
        )

    output = Path(OUTPUT_PATH)

    clean_prices, decisions = clean_data()

    merged = merge_data(clean_prices, source_b)

    output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(output, index=False)

    print(f"Clean rows: {len(clean_prices)}")
    print(f"Merged rows: {len(merged)}")
    print(f"Saved output to {output}")

    return merged


if __name__ == "__main__":
    try:
        run_pipeline()
    except ValueError as exc:
        print(f"Pipeline rejected input: {exc}")
        raise SystemExit(2)