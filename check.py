from src.validate.rules import rule_positive_price, rule_duplicate_ids, rule_duplicate_rows, rule_valid_date, rule_missing_market, rule_known_commodity, rule_negative_rain
from src.ingest.source_a import ingest_source_a
from src.ingest.source_b import (get_all_mkts, get_mkt_rainfall, ingest_source_b)
from src.transform.clean import clean_data
from src.transform.merge import merge_data

import pandas as pd

df = pd.read_csv("data/raw/prices.csv")

neg_prices = rule_positive_price(df)
dupe = rule_duplicate_ids(df)
dub = rule_duplicate_rows(df)
val = rule_valid_date(df)
missing_market = rule_missing_market(df)
commodities = rule_known_commodity(df)

print(neg_prices)
print(dupe)
print(dub)
print(val)
print(missing_market)
print(commodities)
print(df)
print(" ")

source_a = ingest_source_a()
print(f"Source A shape: {source_a.shape}")
print(" ")

source_b = ingest_source_b()
print(f"Source B shape: {source_b.shape}")
print(source_b.head(10))

print(" ")
clean_prices, _ = clean_data()
print(f"Clean prices rows: {len(clean_prices)}")

print(" ")
neg_rain = rule_negative_rain(source_b)
print(f"Neg rain shape: {neg_rain.shape}")
print(" ")

invalid_rain_date = rule_valid_date(source_b)
print(f"Invalid rain dates shape: {invalid_rain_date.shape}")
print(" ")

merge_data = merge_data(clean_prices, source_b)
print(f"Merged shape: {merge_data.shape}")
print(merge_data.head())