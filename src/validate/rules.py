def rule_positive_price(df):
    neg_prices = df[df['price'] < 0].copy()
    neg_prices["reason"] = "Negative price"
    return neg_prices