from pathlib import Path

import pandas as pd
import requests

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

    response = requests.get(RAINFALL_URL, params=params, timeout=10)
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
def get_all_mkts(markets):
    all_market_data = []

    for mkt_name, coordinates in markets.items():
        latitude, longitude = coordinates

        print(f"Fetching data for {mkt_name}...")

        market_data = get_mkt_rainfall(mkt_name, latitude, longitude)
        all_market_data.append(market_data)

    if not all_market_data:
        raise ValueError("No market data!")

    rainfall_data = pd.concat(all_market_data, ignore_index=True)
    output_path = Path(SOURCE_B_RAW_PATH)
    rainfall_data.to_csv(output_path, index=False)
    print(f"Done! Rainfall data saved to {output_path}")

    return rainfall_data


if __name__ == "__main__":
    rain_df = get_all_mkts(MARKET_COORDS)
    print(rain_df.head())
    print(rain_df.shape)