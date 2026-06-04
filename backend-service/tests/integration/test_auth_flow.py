import requests
import sys

BASE_URL = "http://localhost:3001"


def test_auth():
    print("[TEST] Testing Admin Authentication Flow...")
    # Admin login success
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@penguwave.com", "password": "adminpassword"},
    )
    if r.status_code != 200:
        print(f"[TEST] FAIL: Seeded admin login failed ({r.status_code}): {r.text}")
        sys.exit(1)

    data = r.json()
    token = data.get("token")
    if not token or not token.startswith("eyJ"):
        print("[TEST] FAIL: JWT token was not issued correctly or has invalid prefix.")
        sys.exit(1)
    print("[TEST] PASS: Seeded admin successfully authenticated and JWT token issued.")

    # Me endpoint success
    r_me = requests.get(
        f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    if r_me.status_code != 200:
        print(
            f"[TEST] FAIL: Failed to query /api/auth/me ({r_me.status_code}): {r_me.text}"
        )
        sys.exit(1)
    print(f"[TEST] PASS: Authenticated profile details: {r_me.json()}")

    # Invalid token fallback 401
    r_bad = requests.get(
        f"{BASE_URL}/api/auth/me", headers={"Authorization": "Bearer badtoken"}
    )
    if r_bad.status_code != 401:
        print(f"[TEST] FAIL: Expected 401 for bad token, got: {r_bad.status_code}")
        sys.exit(1)
    print(f"[TEST] PASS: Got 401 for invalid token: {r_bad.json()}")

    # Missing header fallback 401
    r_none = requests.get(f"{BASE_URL}/api/auth/me")
    if r_none.status_code != 401:
        print(f"[TEST] FAIL: Expected 401 for missing token, got: {r_none.status_code}")
        sys.exit(1)
    print(f"[TEST] PASS: Got 401 for missing token: {r_none.json()}")


if __name__ == "__main__":
    test_auth()
