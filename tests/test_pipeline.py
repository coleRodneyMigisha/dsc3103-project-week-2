from src.validate.rules import rule_positive_price
from src.transform.merge import merge_data

import pandas as pd


def test_positive_price_rule_rejects_zero_price():
    df = pd.DataFrame({
        "id": ["valid", "invalid"],
        "date": ["2022-01-01", "2022-01-01"],
        "market": ["Bwaise", "Bwaise"],
        "commodity": ["Maize", "Maize"],
        "price": [100, 0],
    })

    rejected = rule_positive_price(df)

    assert rejected["id"].tolist() == ["invalid"]

def test_merge_preserves_price_row_when_rainfall_is_missing():
    prices = pd.DataFrame({
        "id": ["one"],
        "date": ["2022-01-01"],
        "market": ["Bwaise"],
        "commodity": ["Maize"],
        "price": [100],
    })

    rainfall = pd.DataFrame({
        "date": ["2022-01-02"],
        "market": ["Bwaise"],
        "rainfall": [1.5],
    })

    merged = merge_data(prices, rainfall)

    assert len(merged) == 1
    assert merged.loc[0, "id"] == "one"
    assert pd.isna(merged.loc[0, "rainfall"])