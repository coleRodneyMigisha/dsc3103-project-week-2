from urllib import response

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
        "time-zone": "auto",
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
    #for rainfall, mkt_name is key, latitude is value[0], longitude is value[1]
    pass