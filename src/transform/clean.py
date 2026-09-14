import pandas as pd
import parquet as pq
from src.validate import rules

raw_path = 'data/raw/prices.csv'
data_path = 'data/processed/prices_clean.parquet'


def clean_data(path=raw_path):
    df = pd.read_csv(path)

    decisions = []

    neg_p = rules.rule_positive_price(df)
    dup_id = rules.rule_duplicate_ids(df)
    dup_rows = rules.rule_duplicate_rows(df)
    invali_dates = rules.rule_valid_date(df)
    mssng_mrkt = rules.rule_missing_market(df)
    wrng_cmmdt = rules.rule_known_commodity(df)

    reject_index = (neg_p.index.union(dup_id.index).union(dup_rows.index).union(invali_dates.index).union(mssng_mrkt.index))
    for index in reject_index:
        reasons = []
        if index in neg_p.index:
            reasons.append("Negative price")
        if index in dup_id.index:
            reasons.append("Duplicate ID")
        if index in dup_rows.index:
            reasons.append("Duplicate row")
        if index in invali_dates.index:
            reasons.append("Invalid date")
        if index in mssng_mrkt.index:
            reasons.append("Missing market")
        decisions.append({
            'index': index,
            'action': "REJECT",
            'reason': '; '.join(reasons)
        })
    clean_prices = df.drop(index=reject_index).copy()

    for index in wrng_cmmdt.index:
        if index not in reject_index:
            decisions.append({
                'index': index,
                'action': 'NORMALIZE',
                'reason': "Commodity normalize"
            })
    clean_prices['commodity'] = (clean_prices['commodity'].str.strip().str.capitalize())

    decision_log = pd.DataFrame(decisions)
    clean_prices.to_parquet(data_path, index=False)

    print(clean_prices.head())
    print(f"Original rows: {len(df)}")
    print(f"Cleaned rows: {len(clean_prices)}")
    print(f"Missing marks before: {df['market'].isna().sum()}")
    print(f"Missing marks after: {clean_prices['market'].isna().sum()}")
    print(f"Saved to: {data_path}")

    return clean_prices, decision_log

if __name__ == "__main__":
    clean_data()