from rules import rule_positive_price, rule_duplicate_ids, rule_duplicate_rows, rule_valid_date, rule_missing_market, rule_known_commodity
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def plot_histogram(column):
    column = column[column >= 0]

    plt.figure(figsize=(10,7))
    plt.hist(column, bins=50)
    plt.xlabel("Price")
    plt.ylabel("Frequency")
    plt.title("Histogram of price distribution")
    plt.grid(True)
    plt.show()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
df = pd.read_csv(PROJECT_ROOT/'data'/'raw'/'prices.csv')

print("Inferred schema:")
print(df.info())
print(" ")
print(' ')

print(f"Row count: {df.shape[0]} rows")
print(" ")
print(' ')

print("Missing-value count per column:")
print(df.isnull().sum())
print(" ")
print("Confirming with missing market rule:")
print(rule_missing_market(df))
print(" ")
print(' ')

print("Duplicate count:")
print(rule_duplicate_ids(df))
print(rule_duplicate_rows(df))
print(" ")
print(f"Total duplicate count = {len(rule_duplicate_rows(df).index.union(rule_duplicate_ids(df).index))}. Because every duplicate row is a duplicated id, makes sense")
print(" ")
print(" ")

print("Invalid value count:")
print(rule_valid_date(df))
print(rule_positive_price(df))
print(f"Total invalid value row count: {len(rule_positive_price(df).index.union(rule_valid_date(df).index))}")
print(" ")
print(" ")

print("Inconsistent categories (commodities):")
print(rule_known_commodity(df))
print(f"Total inconsistent category rows: {rule_known_commodity(df).shape[0]}")
print(" ")
print(" ")

print("Summary of numerical characteristics:")
print(df.describe())
print(" ")
print(" ")


print("Plot of a histogram for price:")
prices = df["price"]
plot_histogram(prices)
