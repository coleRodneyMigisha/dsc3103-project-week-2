from src.validate.rules import rule_positive_price
import pandas as pd

df = pd.read_csv("data/raw/prices.csv")

neg_prices = rule_positive_price(df)

print(neg_prices)