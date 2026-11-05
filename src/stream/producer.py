import json
import os
import random
import time

import pandas as pd

SRC = "data/processed/prices_with_rainfall.parquet"
BROKER = "data/stream/events.jsonl"   # this is the "broker"
N_EVENTS = 300


def emit_events(n=N_EVENTS):
    df = pd.read_parquet(SRC).dropna(subset=["price"]).reset_index(drop=True)
    os.makedirs(os.path.dirname(BROKER), exist_ok=True)
    open(BROKER, "w").close()

    with open(BROKER, "a") as log:
        for i in range(n):
            row = df.sample(1).iloc[0]
            now = time.time()

            # Line 1: deliberately creates late events (10% chance of 15-40s delay)
            delay = random.uniform(15, 40) if random.random() < 0.10 else 0

            event = {
                "event_id": f"e{i}",
                "market": row["market"],
                "commodity": row["commodity"],
                "price": float(row["price"]),
                "event_time": now - delay,
            }
            line = json.dumps(event) + "\n"
            log.write(line)
            log.flush()

            # Line 2: deliberately creates duplicate events (5% chance of writing the same line twice)
            if random.random() < 0.05:
                log.write(line)
                log.flush()

            time.sleep(random.uniform(0.05, 0.2))
    print("Producer finished:", n, "events")


if __name__ == "__main__":
    emit_events()
