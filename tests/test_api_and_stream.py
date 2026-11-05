import pandas as pd
from src.common.features import make_features, KNOWN_MARKETS, KNOWN_COMMODITIES
from src.stream.consumer import window_start


def test_make_features_produces_expected_contract_columns():
    df = pd.DataFrame([{
        "market": "Owino",
        "commodity": "Maize",
        "date": "2026-03-15",
        "rainfall_mm": None,
    }])
    X = make_features(df)
    expected = (
        ["rainfall_mm", "month"]
        + [f"market_{m}" for m in KNOWN_MARKETS]
        + [f"commodity_{c}" for c in KNOWN_COMMODITIES]
    )
    assert list(X.columns) == expected
    assert X.loc[0, "rainfall_mm"] == 0.0
    assert X.loc[0, "month"] == 3
    assert X.loc[0, "market_Owino"] == 1
    assert X.loc[0, "commodity_Maize"] == 1


def test_window_start_aligns_to_10_second_tumbling_window():
    assert window_start(1762380007.8) == 1762380000
    assert window_start(1762380010.0) == 1762380010
