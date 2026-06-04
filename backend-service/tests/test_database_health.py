import requests
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    print("[TEST] Testing /healthz deep probe endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/healthz")
        print(f"[TEST] Status Code: {r.status_code}")
        print(f"[TEST] Response Body: {r.json()}")
        if r.status_code == 200 and r.json().get("status") == "ok":
            print("[TEST] Health check passed successfully!")
        else:
            print("[TEST] FAIL: Health check returned invalid response.")
            sys.exit(1)
    except Exception as e:
        print(f"[TEST] FAIL: Could not connect to API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_health()
