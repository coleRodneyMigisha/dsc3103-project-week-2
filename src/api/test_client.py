import requests

BASE = "http://localhost:8000"

valid = {"market": "Owino", "commodity": "Maize", "date": "2026-03-15", "rainfall_mm": 4.2}
invalid = {"market": "Owino", "commodity": "Maize", "date": "2026-03-15", "rainfall_mm": -5}


def show(title, response):
    print(f"--- {title}: HTTP {response.status_code}")
    print(response.json())


if __name__ == "__main__":
    show("health", requests.get(f"{BASE}/health"))
    # TODO: call /predict with the valid request and show the result
    show("valid predict", requests.post(f"{BASE}/predict", json=valid))
    # TODO: call /predict with an INVALID request (e.g. rainfall_mm = -5) and show the result
    show("invalid predict", requests.post(f"{BASE}/predict", json=invalid))
