from src.validate.rules import rule_positive_price, rule_duplicate_ids, rule_duplicate_rows, rule_valid_date, rule_missing_market, rule_known_commodity
from src.ingest.source_a import ingest_source_a
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