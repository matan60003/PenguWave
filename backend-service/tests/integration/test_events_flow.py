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
    # Handle both old and new login response payload schemas (token/access_token)
    login_data = r.json()
    token = login_data.get("token") or login_data.get("access_token")
    if not token:
        log("FAIL: Token not found in login response.")
        sys.exit(1)
    headers = {"Authorization": f"Bearer {token}"}
    log("Admin logged in successfully.")

    # 2. Get initial events count
    log("Retrieving initial events...")
    r = requests.get(f"{BASE_URL}/api/events", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Failed to list initial events ({r.status_code}): {r.text}")
        sys.exit(1)
    initial_events = r.json()
    initial_count = len(initial_events)
    log(f"PASS: Listed {initial_count} initial events.")

    # Validate schema fields on first event
    if initial_count > 0:
        first_event = initial_events[0]
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

    # 3. Create a new security event (POST)
    log("Creating a new security event...")
    new_event_payload = {
        "timestamp": "2026-06-04T16:00:00Z",
        "severity": "CRITICAL",
        "title": "Unauthorized DB Access Attempt",
        "description": "Multiple unauthorized connection attempts detected on database cluster from unrecognized subnet.",
        "assetHostname": "prod-db-01.penguwave.internal",
        "assetIp": "10.0.2.10",
        "sourceIp": "192.168.42.12",
        "tags": ["database", "intrusion", "critical"],
        "userId": "usr-admin",
    }
    r = requests.post(f"{BASE_URL}/api/events", json=new_event_payload, headers=headers)
    if r.status_code != 201:
        log(f"FAIL: Event creation failed ({r.status_code}): {r.text}")
        sys.exit(1)
    created_event = r.json()
    created_id = created_event.get("id")
    if not created_id or not created_id.startswith("evt-"):
        log(f"FAIL: Created event has invalid ID: {created_id}")
        sys.exit(1)
    log(f"PASS: Security event created with ID: {created_id}")

    # 4. Verify count increased by 1
    log("Verifying events count increased...")
    r = requests.get(f"{BASE_URL}/api/events", headers=headers)
    current_events = r.json()
    if len(current_events) != initial_count + 1:
        log(f"FAIL: Expected {initial_count + 1} events, got {len(current_events)}")
        sys.exit(1)
    log("PASS: Event list correctly contains the newly created event.")

    # 5. Fetch single event by ID
    log(f"Retrieving single event by ID: {created_id}...")
    r = requests.get(f"{BASE_URL}/api/events/{created_id}", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Failed to fetch event by ID ({r.status_code}): {r.text}")
        sys.exit(1)
    single_event = r.json()
    if (
        single_event["id"] != created_id
        or single_event["title"] != new_event_payload["title"]
    ):
        log("FAIL: Returned event details do not match.")
        sys.exit(1)
    log(f"PASS: Successfully retrieved event: {single_event['title']}")

    # 6. Test severity filtering (filtering by the new CRITICAL severity)
    log("Retrieving only CRITICAL severity events...")
    r = requests.get(f"{BASE_URL}/api/events?severity=CRITICAL", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Severity filtering failed ({r.status_code}): {r.text}")
        sys.exit(1)
    critical_events = r.json()
    if len(critical_events) != 1 or critical_events[0]["id"] != created_id:
        log(f"FAIL: Expected exactly 1 CRITICAL event, got {len(critical_events)}")
        sys.exit(1)
    log("PASS: Filtered CRITICAL severity events successfully.")

    # 7. Test pagination
    log("Retrieving paginated events (limit=5, offset=10)...")
    r = requests.get(f"{BASE_URL}/api/events?limit=5&offset=10", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Pagination failed ({r.status_code}): {r.text}")
        sys.exit(1)
    paginated_events = r.json()
    if len(paginated_events) != 5:
        log(f"FAIL: Expected exactly 5 events, got {len(paginated_events)}")
        sys.exit(1)
    log("PASS: Pagination limits and offsets sliced successfully.")

    # 8. Clean up created event (DELETE) to ensure database isolation
    log(f"Deleting test security event ID: {created_id}...")
    r = requests.delete(f"{BASE_URL}/api/events/{created_id}", headers=headers)
    if r.status_code != 200:
        log(f"FAIL: Deleting event failed ({r.status_code}): {r.text}")
        sys.exit(1)
    log("PASS: Test security event deleted successfully.")

    # 9. Verify count is restored
    log("Verifying events count restored to initial size...")
    r = requests.get(f"{BASE_URL}/api/events", headers=headers)
    final_events = r.json()
    if len(final_events) != initial_count:
        log(
            f"FAIL: Expected count to return to {initial_count}, got {len(final_events)}"
        )
        sys.exit(1)
    log("PASS: Database is fully clean and isolated.")

    # 10. Retrieve non-existent event by ID (should get 404)
    log("Retrieving non-existent event ID (should get 404)...")
    r = requests.get(f"{BASE_URL}/api/events/evt-non-existent", headers=headers)
    if r.status_code != 404:
        log(f"FAIL: Expected 404 for missing event, got {r.status_code}")
        sys.exit(1)
    log(f"PASS: Got 404 Event Not Found with body: {r.json()}")

    # 11. Unauthenticated request (should get 401)
    log("Retrieving events without token (should get 401)...")
    r = requests.get(f"{BASE_URL}/api/events")
    if r.status_code != 401:
        log(f"FAIL: Expected 401 for unauthenticated request, got {r.status_code}")
        sys.exit(1)
    log(f"PASS: Got 401 Unauthorized with body: {r.json()}")

    # 12. Invalid token request (should get 401)
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
