import uuid

PASSWORD = "Passw0rd123"
SEED_PASSWORD = "Seed12345"
API = "/api/v1"


def new_username(prefix: str = "u") -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def signup(client, username: str | None = None, password: str = PASSWORD):
    username = username or new_username()
    response = client.post(
        f"{API}/auth/signup",
        json={
            "username": username,
            "email": f"{username}@test.example",
            "full_name": "Test User",
            "password": password,
        },
    )
    return username, response


def login(client, username: str, password: str = PASSWORD):
    return client.post(f"{API}/auth/login", json={"username": username, "password": password})


def make_user(client) -> str:
    username, response = signup(client)
    assert response.status_code == 201, response.text
    return username


def login_ok(client, username: str, password: str = PASSWORD) -> dict:
    """Log in and return {'token': access token, 'id': user id, 'headers': auth header}."""
    response = login(client, username, password)
    assert response.status_code == 200, response.text
    body = response.json()
    return {
        "token": body["access_token"],
        "id": body["user"]["id"],
        "headers": {"Authorization": f"Bearer {body['access_token']}"},
    }


def new_user(client) -> dict:
    """Sign up + log in a brand-new user."""
    username = make_user(client)
    info = login_ok(client, username)
    info["username"] = username
    return info


def admin_login(client, name: str = "admin1") -> dict:
    return login_ok(client, name, SEED_PASSWORD)


PRODUCT = {"name": "Test item", "price": "10.00", "stock": 5, "category": "test"}
