import pandas as pd
import matplotlib.pyplot as plt
import os
from src.validate import rules

raw_path = 'data/raw/prices.csv'

PLOT_PATH = 'src/validate/histogram plot/'
os.makedirs(PLOT_PATH, exist_ok=True)

def inferred_schema(df):
    print("Inferred Schema:")
    print(df.dtypes)
    print(" ")

def row_count(df):
    print(f"Row Count: {len(df)}")
    print(" ")

def missing_count(df):
    print(f"Missing Value Count: {len(rules.rule_missing_market(df))}")
    print(" ")

def duplicate_count(df):
    print(f"Duplicate Count: {len(rules.rule_duplicate_ids(df))}")
    print(f"That's the total duplicate IDs but only {len(rules.rule_duplicate_rows(df))} are exactly duplicate rows")
    print(" ")

def invalid_count(df):
    print(f"Invalid Value Count: {len(rules.rule_valid_date(df)) + len(rules.rule_positive_price(df))}")
    print(f"{len(rules.rule_valid_date(df))} are the invalid dates and {len(rules.rule_positive_price(df))} are the negative prices")
    print(" ")

def inconsistent_count(df):
    print(f"Inconsistent Categories: {len(rules.rule_known_commodity(df))}")
    print("(These are the inconsistent commodity names)")
    print(" ")

def stats(df):
    print(f"Statistics for Numerical Columns:")
    print(f"{df.describe()}")

def plot_histogram(column):
    column = column[column >= 0]

    plt.figure(figsize=(10,7))
    plt.hist(column, bins=50)
    plt.xlabel("Price")
    plt.ylabel("Frequency")
    plt.title("Histogram of price distribution")
    plt.grid(True)
    h = os.path.join(PLOT_PATH, 'histogram.png')
    plt.savefig(h, bbox_inches='tight')
    plt.show()
    plt.close()

def plot(df):
    prices = df["price"]
    plot_histogram(prices)




def run_files(path = raw_path):
    df = pd.read_csv(path)
    inferred_schema(df)
    row_count(df)
    missing_count(df)
    duplicate_count(df)
    invalid_count(df)
    inconsistent_count(df)
    stats(df)
    plot(df)

if __name__ == "__main__":
    run_files()