#%%
import csv
import random
from datetime import datetime, timedelta


random.seed(42)
base_date = datetime(2020, 1, 1)
wrong_dates = ["2020-14-50", "2021-13-49", "2022-15-48", "2023-16-47", "2024-17-45", "2025-18-37", "2026-19-40"]
markets = ["Mukono", "Bwaise", "Nakasero", "Kansanga", None]
commodities = ["maize", "Maize", "MAIZE", "eggs", "beans", "Beans", "Cassava", "CASSAVA", "fish", "banana leaves"]

rows = []

for i in range(10000):
    row = {
        "id" : f'fd-{i}' if random.random()>0.02 else f'fd-{i-1}',
        "date" : (base_date + timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d") if random.random()>0.03 else random.choice(wrong_dates),
        "market" : random.choice(markets),
        "commodity" : random.choice(commodities),
        "price" : ((random.randint(500, 25000))//100)*100 if random.random()>0.05 else ((random.randint(-5000, -1000))//100)*100
    }
    if random.random()>0.075:
        rows.append(row)
    else:
        rows.append(row)
        rows.append(row)


with open("data/raw/prices.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["id", "date", "market", "commodity", "price"])
    writer.writeheader()
    writer.writerows(rows)