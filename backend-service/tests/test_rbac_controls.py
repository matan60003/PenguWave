import requests
import sys

BASE_URL = "http://localhost:3001"


def log(msg):
    print(f"[TEST] {msg}")


def run_tests():
    # 1. Admin login
    log("Logging in as admin...")
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@penguwave.com", "password": "adminpassword"},
    )
    if r.status_code != 200:
        log(f"FAIL: Admin login failed ({r.status_code}): {r.text}")
        sys.exit(1)
    admin_token = r.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    log("Admin logged in successfully.")

    # 2. Admin creates a new analyst user
    log("Admin creating a new analyst user...")
    r = requests.post(
        f"{BASE_URL}/api/users",
        headers=admin_headers,
        json={
            "email": "analyst@penguwave.com",
            "password": "analystpassword",
            "role": "analyst",
        },
    )
    if r.status_code != 201:
        log(f"FAIL: Failed to create user ({r.status_code}): {r.text}")
        sys.exit(1)
    analyst_id = r.json()["id"]
    log(f"Created analyst user successfully with ID: {analyst_id}")

    # 3. Analyst login
    log("Logging in as the new analyst...")
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "analyst@penguwave.com", "password": "analystpassword"},
    )
    if r.status_code != 200:
        log(f"FAIL: Analyst login failed ({r.status_code}): {r.text}")
        sys.exit(1)
    analyst_token = r.json()["token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    log("Analyst logged in successfully.")

    # 4. Analyst attempts to list users (should get 403)
    log("Analyst attempting to GET /api/users (should get 403)...")
    r = requests.get(f"{BASE_URL}/api/users", headers=analyst_headers)
    if r.status_code != 403:
        log(
            f"FAIL: Expected 403 for analyst GET /api/users, got {r.status_code}: {r.text}"
        )
        sys.exit(1)
    log(f"PASS: Got 403 Forbidden with body: {r.json()}")

    # 5. Analyst attempts to create a user (should get 403)
    log("Analyst attempting to POST /api/users (should get 403)...")
    r = requests.post(
        f"{BASE_URL}/api/users",
        headers=analyst_headers,
        json={
            "email": "hacker@penguwave.com",
            "password": "hackerpassword",
            "role": "admin",
        },
    )
    if r.status_code != 403:
        log(
            f"FAIL: Expected 403 for analyst POST /api/users, got {r.status_code}: {r.text}"
        )
        sys.exit(1)
    log(f"PASS: Got 403 Forbidden with body: {r.json()}")

    # 6. Admin lists all users
    log("Admin listing all users (should succeed)...")
    r = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
    if r.status_code != 200:
        log(f"FAIL: Admin failed to list users ({r.status_code}): {r.text}")
        sys.exit(1)
    users = r.json()
    log(f"PASS: Admin list returned {len(users)} users.")
    # Ensure no hashed_password is leaked
    for u in users:
        if "hashed_password" in u or "password" in u:
            log("FAIL: Security leak! User schema exposes password field.")
            sys.exit(1)
    log("PASS: No password details leaked in user response payload.")

    # 7. Admin updates analyst user (PATCH)
    log("Admin updating analyst status to suspended...")
    r = requests.patch(
        f"{BASE_URL}/api/users/{analyst_id}",
        headers=admin_headers,
        json={"status": "suspended"},
    )
    if r.status_code != 200:
        log(f"FAIL: Admin failed to update user ({r.status_code}): {r.text}")
        sys.exit(1)
    log(f"PASS: Analyst updated to suspended: {r.json()}")

    # 8. Admin attempts self-deletion (should get 400)
    log("Admin attempting self-deletion (should get 400)...")
    r = requests.delete(f"{BASE_URL}/api/users/usr-admin", headers=admin_headers)
    if r.status_code != 400:
        log(f"FAIL: Expected 400 for self-deletion, got {r.status_code}: {r.text}")
        sys.exit(1)
    log(f"PASS: Got 400 Bad Request with body: {r.json()}")

    # 9. Admin deletes the analyst user (should succeed)
    log("Admin deleting analyst user...")
    r = requests.delete(f"{BASE_URL}/api/users/{analyst_id}", headers=admin_headers)
    if r.status_code != 200:
        log(f"FAIL: Admin failed to delete analyst ({r.status_code}): {r.text}")
        sys.exit(1)
    log(f"PASS: Analyst deleted successfully: {r.json()}")

    # 10. Admin attempts to delete non-existent user (should get 404)
    log("Admin attempting to delete non-existent user (should get 404)...")
    r = requests.delete(f"{BASE_URL}/api/users/non-existent", headers=admin_headers)
    if r.status_code != 404:
        log(
            f"FAIL: Expected 404 for non-existent user deletion, got {r.status_code}: {r.text}"
        )
        sys.exit(1)
    log(f"PASS: Got 404 Not Found with body: {r.json()}")

    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    run_tests()
