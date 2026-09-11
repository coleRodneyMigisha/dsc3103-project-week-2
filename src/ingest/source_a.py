import pandas as pd

from src.common.config import SOURCE_A_RAW_PATH


def ingest_source_a(path=SOURCE_A_RAW_PATH):
    df = pd.read_csv(path)
    return df