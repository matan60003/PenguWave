from app.core import security


def test_hash_password():
    password = "supersecretpassword123!"
    hashed = security.hash_password(password)

    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")  # bcrypt prefixes


def test_verify_password_correct():
    password = "supersecretpassword123!"
    hashed = security.hash_password(password)

    assert security.verify_password(password, hashed) is True


def test_verify_password_incorrect():
    password = "supersecretpassword123!"
    wrong_password = "wrongpassword"
    hashed = security.hash_password(password)

    assert security.verify_password(wrong_password, hashed) is False


def test_verify_password_empty_input():
    password = "supersecretpassword123!"
    hashed = security.hash_password(password)

    assert security.verify_password("", hashed) is False


def test_hash_password_empty():
    password = ""
    hashed = security.hash_password(password)

    assert security.verify_password("", hashed) is True
