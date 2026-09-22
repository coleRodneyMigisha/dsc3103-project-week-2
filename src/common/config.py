SOURCE_A_RAW_PATH = "data/raw/prices.csv"
SOURCE_B_RAW_PATH = "data/raw/rain.csv"

OUTPUT_PATH = "data/processed/prices_with_rain.parquet"

MARKET_COORDS = {
    "Mukono": (0.3533, 32.7553),
    "Bwaise": (0.3500, 32.5611),
    "Nakasero": (0.3233, 32.5789),
    "Kansanga": (0.2872, 32.6078)
}

RAINFALL_START_DATE = "2020-01-01"
RAINFALL_END_DATE = "2022-12-31"

RAINFALL_URL = "https://archive-api.open-meteo.com/v1/archive"