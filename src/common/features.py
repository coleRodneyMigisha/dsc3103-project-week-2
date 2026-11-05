import pandas as pd

# The model's contract: these lists and this column order are FIXED.
KNOWN_MARKETS = ["Owino", "Nakasero", "Kalerwe", "Mbale Central", "Gulu Main", "Unknown"]
KNOWN_COMMODITIES = ["Maize", "Beans", "Cassava", "Rice"]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn raw rows (market, commodity, date, rainfall_mm) into model inputs.

    Used by BOTH training and the API, so the two can never disagree.
    """
    out = pd.DataFrame(index=df.index)

    out["rainfall_mm"] = df["rainfall_mm"].fillna(0.0)
    out["month"] = pd.to_datetime(df["date"]).dt.month

    for m in KNOWN_MARKETS:
        out[f"market_{m}"] = (df["market"] == m).astype(int)
    for c in KNOWN_COMMODITIES:
        out[f"commodity_{c}"] = (df["commodity"] == c).astype(int)

    return out
