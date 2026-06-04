import requests
import sys

BASE_URL = "http://localhost:3001"


def log(msg):
    print(f"[TEST] {msg}")


def run_tests():
    # 1. Login as admin
    log("Logging in as admin...")
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@penguwave.com", "password": "adminpassword"},
    )
    if r.status_code != 200:
        log(f"FAIL: Admin login failed ({r.status_code}): {r.text}")
        sys.exit(1)
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("Admin logged in successfully.")

    # 2. Get all events
    log("Retrieving all events (should succeed)...")
    r = requests.get(f"{BASE_URL}/api/events", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Failed to list events ({r.status_code}): {r.text}")
        sys.exit(1)
    events = r.json()
    log(f"PASS: Listed {len(events)} events.")
    if len(events) == 0:
        log("FAIL: Expected non-empty list of events.")
        sys.exit(1)

    # Validate schema fields
    first_event = events[0]
    expected_fields = {
        "id",
        "timestamp",
        "severity",
        "title",
        "description",
        "assetHostname",
        "assetIp",
        "sourceIp",
        "tags",
        "userId",
    }
    for field in expected_fields:
        if field not in first_event:
            log(f"FAIL: Missing field '{field}' in Event Response.")
            sys.exit(1)
    log("PASS: Event payload schema conforms to EventResponse.")

    # 3. Test severity filtering
    log("Retrieving only HIGH severity events...")
    r = requests.get(f"{BASE_URL}/api/events?severity=HIGH", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Severity filtering failed ({r.status_code}): {r.text}")
        sys.exit(1)
    high_events = r.json()
    for e in high_events:
        if e.get("severity") != "HIGH":
            log(f"FAIL: Event severity is not HIGH: {e}")
            sys.exit(1)
    log(f"PASS: Filtered {len(high_events)} HIGH severity events successfully.")

    # 4. Test pagination
    log("Retrieving paginated events (limit=5, offset=10)...")
    r = requests.get(f"{BASE_URL}/api/events?limit=5&offset=10", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Pagination failed ({r.status_code}): {r.text}")
        sys.exit(1)
    paginated_events = r.json()
    if len(paginated_events) != 5:
        log(f"FAIL: Expected exactly 5 events, got {len(paginated_events)}")
        sys.exit(1)
    # Match against the full list
    if paginated_events[0]["id"] != events[10]["id"]:
        log("FAIL: Pagination offset matching failed.")
        sys.exit(1)
    log("PASS: Pagination limits and offsets sliced successfully.")

    # 5. Retrieve single event by ID
    target_id = first_event["id"]
    log(f"Retrieving single event by ID: {target_id}...")
    r = requests.get(f"{BASE_URL}/api/events/{target_id}", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Failed to fetch event by ID ({r.status_code}): {r.text}")
        sys.exit(1)
    single_event = r.json()
    if single_event["id"] != target_id:
        log("FAIL: Returned event ID does not match.")
        sys.exit(1)
    log(f"PASS: Successfully retrieved event: {single_event['title']}")

    # 6. Retrieve non-existent event by ID (should get 404)
    log("Retrieving non-existent event ID (should get 404)...")
    r = requests.get(f"{BASE_URL}/api/events/evt-non-existent", headers=headers)
    if r.status_code != 404:
        log(f"FAIL: Expected 404 for missing event, got {r.status_code}")
        sys.exit(1)
    log(f"PASS: Got 404 Event Not Found with body: {r.json()}")

    # 7. Unauthenticated request (should get 401)
    log("Retrieving events without token (should get 401)...")
    r = requests.get(f"{BASE_URL}/api/events")
    if r.status_code != 401:
        log(f"FAIL: Expected 401 for unauthenticated request, got {r.status_code}")
        sys.exit(1)
    log(f"PASS: Got 401 Unauthorized with body: {r.json()}")

    # 8. Invalid token request (should get 401)
    log("Retrieving events with bad token (should get 401)...")
    r = requests.get(
        f"{BASE_URL}/api/events", headers={"Authorization": "Bearer badtoken"}
    )
    if r.status_code != 401:
        log(f"FAIL: Expected 401 for bad token request, got {r.status_code}")
        sys.exit(1)
    log(f"PASS: Got 401 Unauthorized with body: {r.json()}")

    print("\n[ALL EVENTS TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    run_tests()
