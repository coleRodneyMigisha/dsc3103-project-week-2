import pandas as pd

def rule_positive_price(df):
    neg_prices = df[df['price'] <= 0].copy()
    neg_prices["reason"] = "Negative price"
    return neg_prices

def rule_duplicate_ids(df):
    duplicate_ids = df[df['id'].duplicated()].copy()
    duplicate_ids["reason"] = "Duplicate id"
    return duplicate_ids

def rule_duplicate_rows(df):
    duplicate_rows = df[df.duplicated()].copy()
    duplicate_rows["reason"] = "Duplicate row"
    return duplicate_rows

def rule_valid_date(df):
    valid_dates = df.copy()
    parsed_dates = pd.to_datetime(valid_dates['date'], errors='coerce', format='%Y-%m-%d')
    valid_dates["valid_dates"] = parsed_dates.notna()
    invalid_dates = valid_dates[~valid_dates["valid_dates"]]
    invalid_dates["reason"] = "Invalid date"
    return invalid_dates

def rule_missing_market(df):
    missing_markets = df[df['market'].isnull()].copy()
    missing_markets["reason"] = "Missing market"
    return missing_markets

def rule_known_commodity(df):
    wrong_format = df[df['commodity'].notna() & (df['commodity']!=df['commodity'].str.strip().str.capitalize())].copy()
    wrong_format["reason"] = "Wrong commodity"
    return wrong_format

def rule_negative_rain(df):
    neg_rain = df[df['rainfall'] < 0].copy()
    neg_rain["reason"] = "Negative price"
    return neg_rain