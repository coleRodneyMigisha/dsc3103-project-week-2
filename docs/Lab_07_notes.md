# DSC3103 — Lab 9 (Streaming and Event-Driven Data Systems) Notes

### Step 1 — Late and Duplicate Events in `producer.py`

**Two lines that deliberately create late events and duplicate events:**
- **Late events:** `delay = random.uniform(15, 40) if random.random() < 0.10 else 0` followed by `"event_time": now - delay` (10% of events are stamped with an `event_time` 15 to 40 seconds earlier than `now`).
- **Duplicate events:** `if random.random() < 0.05: log.write(line); log.flush()` (5% of events are written to the broker log a second time with the exact same `event_id`).

**Question:** Why does the producer sometimes make `event_time` earlier than the current time? Give an example of this scenario in the real-world.
- Because in real-world systems, the time an event actually occurred (`event_time`) is often earlier than the time the server receives it (`processing_time`) due to network delays or offline buffering.
- **Real-world example:** A market price clerk in a rural market (e.g. Gulu Main or Mbale Central) records a maize price on a mobile app at `10:00:05` while mobile network coverage is down; when the phone regains signal 30 seconds later, the event arrives at the broker at `10:00:35` with `event_time = 10:00:05`.

---

### Step 3 — Window Output Timing

**Question:** Does a window's result appear **immediately** after the window ends? Why not? What is the delay, and which constant controls it?
- No, a window's result does **not** appear immediately after the 10-second window ends.
- It waits because out-of-order (late) events belonging to that window might still be in transit.
- The delay after the window ends is **20 seconds** (so 30 seconds total after `window_start`, i.e. `now >= ws + WINDOW + WATERMARK`), and it is controlled by the `WATERMARK = 20` constant.

---

### Step 4 — Event Time vs Processing Time

**Question:** Using **your** output, if the window logic used the time the consumer **received** each event instead of `event_time`, which of your windows would have the wrong count, and why?
- In our run (`WATERMARK = 20`), **all 6 windows** had different counts under processing time vs event time:
  - `Window 1762379980`: event-time count = `3`, processing-time count = `0`
  - `Window 1762379990`: event-time count = `5`, processing-time count = `0`
  - `Window 1762380000`: event-time count = `79`, processing-time count = `83`
  - `Window 1762380010`: event-time count = `76`, processing-time count = `81`
  - `Window 1762380020`: event-time count = `72`, processing-time count = `80`
  - `Window 1762380030`: event-time count = `53`, processing-time count = `56`
- **Why:** Delayed events that actually happened in an earlier window (such as `1762379980` or `1762380000`) arrived 15–40 seconds later. Under processing time, they get falsely bucketed into whichever later window (`1762380000`–`1762380030`) happens to be open when they arrive, inflating the later windows and under-counting the earlier windows.

---

### Step 5 — Late Events and Watermark Trade-off

1. **With `WATERMARK = 20`:**
   - **Late events routed to `late_events.jsonl`:** `12` events (their delay exceeded `WINDOW + WATERMARK` so their window had already closed).
   - **Late events accepted into their correct window:** `13` delayed events arrived before `ws + 10 + 20` and were counted in their true event-time window.

2. **Watermark comparison table:**

| WATERMARK | Late events logged | Delay before a window prints |
|---|---|---|
| 5 | 25 | 5s after window end (15s after `ws`) |
| 20 | 12 | 20s after window end (30s after `ws`) |
| 40 | 0 | 40s after window end (50s after `ws`) |

**Question:** Which setting would you choose for a fraud alert, and which for a daily price report? Why?
- **For a fraud alert:** I would choose **`WATERMARK = 5`** (short watermark) because speed is critical — we need to flag suspicious activity within seconds before a fraudster cashes out, even if a few very delayed events have to be handled separately on a side output.
- **For a daily price report:** I would choose **`WATERMARK = 40`** (long watermark) because completeness and accuracy matter much more than a 40-second delay when computing official market price averages.

---

### Step 6 — Duplicates and State Growth

1. **How many duplicates were caught (`duplicate_events.jsonl`)?**
   - `11` duplicate events were caught and logged to `data/stream/duplicate_events.jsonl`.
2. **Comment out the code for duplicates and run again. How do the window counts change?**
   - The window counts increase by the duplicate events (`Window 1762380000` increases from `79` to `83`, `Window 1762380010` from `76` to `80`, `Window 1762380020` from `72` to `74`, and `Window 1762380030` from `53` to `54`), double-counting prices and distorting the window mean.
3. **`seen_ids` grows forever. For a stream of 10 million events a day, what would happen to it? Suggest one way to limit it, and say what risk your limit creates.**
   - **What would happen:** `seen_ids` is an in-memory Python `set`, so at 10 million IDs per day it would consume gigabytes of RAM and eventually crash the consumer with an Out-Of-Memory (`MemoryError`) failure.
   - **How to limit it:** Keep only `event_id`s from a bounded time-to-live (TTL) window (e.g. expire IDs older than `WINDOW + WATERMARK`, or store a fixed-size LRU / sliding time cache of the last 5 minutes).
   - **Risk created:** If a duplicate retry arrives *after* its `event_id` has expired from the cache, the consumer will not recognise it as a duplicate and will process it a second time (though if its `event_time` is old, the watermark check will still catch it as a late event).

---

### Step 7 — Stopping and Restarting the Consumer

1. **What happened to `offset`, `windows` and `seen_ids`?**
   - Because they were stored only in volatile RAM variables inside the Python process, stopping the consumer (`Ctrl+C`) wiped `offset` back to `0`, emptied `windows = {}`, and cleared `seen_ids = set()`.
2. **What does the restarted consumer do with events it had already counted?**
   - Since `offset` resets to `0`, the restarted consumer re-reads `data/stream/events.jsonl` from line 0 and re-processes all old events again (and because `now` is now much later than their `event_time`, it marks old finalised windows' events as late!).
3. **What would you have to save (checkpoint) so that a restart continues correctly?**
   - We must atomically checkpoint: (a) the file `offset` (line number read so far), (b) the open `windows` state (`n` and `total` per window start), (c) the `finalised` window set, and (d) the recent `seen_ids` set to durable disk/database storage.

---

### Step 8 — When is a 5-Minute Batch Job Enough vs Streaming?

- **When a 5-minute batch job is good enough:** For a public market-price dashboard or daily bulletin showing average commodity prices across Owino, Nakasero, and Mukono. Physical food prices in open-air markets change gradually over hours or days, so a 5-minute refresh has zero business downside and is much simpler to maintain.
- **When you need streaming:** When automated actions or alerts depend on immediate event detection — for example, detecting flash price manipulation/collusion in real time, triggering instant automated logistics bidding when supply drops at a market, or catching anomalous/fraudulent mobile-money commodity payments before settlement completes.
