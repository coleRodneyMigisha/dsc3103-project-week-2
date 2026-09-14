from pathlib import Path

import pandas as pd
import requests
import time
import os

from src.common.config import (
    SOURCE_B_RAW_PATH,
    MARKET_COORDS,
    RAINFALL_START_DATE,
    RAINFALL_END_DATE,
    RAINFALL_URL
)


def get_mkt_rainfall(mkt_name, latitude, longitude, start_date=RAINFALL_START_DATE, end_date=RAINFALL_END_DATE):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "auto",
        "daily": "precipitation_sum"
    }

    response = requests.get(RAINFALL_URL, params=params, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get data for {mkt_name}: Status  {response.status_code}"
        )

    daily = response.json()["daily"]
    return pd.DataFrame({
        "date": daily["time"],
        "market": mkt_name,
        "rainfall": daily["precipitation_sum"]
        })

#write function to get rain information for all markets
def get_all_mkts(markets=MARKET_COORDS):
    all_market_data = []

    for mkt_name, coordinates in markets.items():
        latitude, longitude = coordinates

        print(f"Fetching data for {mkt_name}...")

        market_data = get_mkt_rainfall(mkt_name, latitude, longitude)
        all_market_data.append(market_data)
        time.sleep(5)

    if not all_market_data:
        raise ValueError("No market data!")

    rain_data = pd.concat(all_market_data, ignore_index=True)

    return rain_data

def ingest_source_b(path=SOURCE_B_RAW_PATH):
    if os.path.exists(path):
        return pd.read_csv(path)

    df_b = get_all_mkts()
    df_b.csv(path, index=False)
    return df_b