import pandas as pd
from src.validate import rules

raw_path = 'data/raw/prices.csv'

def inferred_schema(df):
    print("Inferred Schema:")
    print(df.dtypes)
    print(" ")

def row_count(df):
    print(f"Row Count: {len(df)}")
    print(" ")

def neg_values(df):
    print(f"Negative Values: {len(rules.rule_positive_price(df))}")




def run_files(path = raw_path):
    df = pd.read_csv(path)
    inferred_schema(df)
    row_count(df)
    neg_values(df)

if __name__ == "__main__":
    run_files()