"""Authentication: signup, login, tokens, refresh, logout, sessions, lockout."""

import base64
import json
import time

import jwt

from core import config, security
from tests.helpers import API, PASSWORD, login, login_ok, make_user, new_user, new_username, signup


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


# ------------------------------------------------------------------ FR-AUTH-01


def test_signup_creates_user_without_password_in_response(client):
    """FR-AUTH-01"""
    username, response = signup(client)
    body = response.json()
    assert response.status_code == 201
    assert body["username"] == username
    assert body["role"] == "user"
    assert "password" not in body and "password_hash" not in body


def test_signup_cannot_choose_role(client):
    """FR-AUTH-01: nobody can make themselves admin at signup."""
    username = new_username()
    response = client.post(
        f"{API}/auth/signup",
        json={
            "username": username,
            "email": f"{username}@test.example",
            "full_name": "Sneaky",
            "password": PASSWORD,
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_signup_rejects_weak_passwords(client):
    """FR-AUTH-01"""
    assert signup(client, password="short1")[1].status_code == 422  # too short
    assert signup(client, password="onlyletters")[1].status_code == 422  # no digit


def test_signup_duplicate_username_is_409(client):
    """FR-AUTH-01"""
    username = make_user(client)
    _, response = signup(client, username)
    assert response.status_code == 409
    assert response.json()["error_code"] == "USERNAME_TAKEN"


# ------------------------------------------------------------------ FR-AUTH-02


def test_login_returns_access_token_with_claims_and_cookie(client):
    """FR-AUTH-02: token claims, 15 minute lifetime and the httpOnly refresh cookie."""
    username = make_user(client)
    response = login(client, username)
    assert response.status_code == 200
    token = response.json()["access_token"]
    claims = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    assert {"sub", "role", "sid", "iat", "exp"} <= set(claims)
    assert claims["role"] == "user"
    assert claims["exp"] - claims["iat"] == config.ACCESS_TOKEN_MINUTES * 60
    set_cookie = response.headers["set-cookie"].lower()
    assert "refresh_token=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=strict" in set_cookie


# ------------------------------------------------------------------ FR-AUTH-03


def test_wrong_password_and_unknown_user_look_the_same(client):
    """FR-AUTH-03: the error does not reveal which usernames exist."""
    username = make_user(client)
    wrong_password = login(client, username, "Wrong12345")
    unknown_user = login(client, new_username("nobody"), "Wrong12345")
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


# ------------------------------------------------------------------ FR-AUTH-04


def test_lockout_after_five_failed_logins(client):
    """FR-AUTH-04: the 6th attempt is refused even with the right password."""
    username = make_user(client)
    for _ in range(5):
        assert login(client, username, "Wrong12345").status_code == 401
    response = login(client, username, PASSWORD)
    assert response.status_code == 429
    assert response.json()["error_code"] == "TOO_MANY_ATTEMPTS"


# ------------------------------------------------------------------ FR-AUTH-05


def test_password_hash_is_salted_peppered_and_verifiable():
    """FR-AUTH-05"""
    first = security.hash_password(PASSWORD)
    second = security.hash_password(PASSWORD)
    assert first != second  # random salt
    assert PASSWORD not in first
    assert security.verify_password(PASSWORD, first)
    assert not security.verify_password("Another12345", first)


# ------------------------------------------------------------------ FR-AUTH-06


def test_refresh_gives_new_access_token_and_rotates_cookie(client):
    """FR-AUTH-06"""
    username = make_user(client)
    login_ok(client, username)
    old_cookie = client.cookies.get("refresh_token")
    response = client.post(f"{API}/auth/refresh")
    assert response.status_code == 200
    new_cookie = client.cookies.get("refresh_token")
    assert new_cookie and new_cookie != old_cookie
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get(f"{API}/auth/me", headers=headers).status_code == 200


def test_refresh_without_cookie_is_401(client):
    """FR-AUTH-06"""
    response = client.post(f"{API}/auth/refresh")
    assert response.status_code == 401
    assert response.json()["error_code"] == "REFRESH_TOKEN_INVALID"


# ------------------------------------------------------------------ FR-AUTH-07


def test_reusing_an_old_refresh_token_closes_the_session(client, make_client):
    """FR-AUTH-07: a replayed (stolen) refresh token kills the whole session."""
    username = make_user(client)
    first = login_ok(client, username)
    old_cookie = client.cookies.get("refresh_token")
    assert client.post(f"{API}/auth/refresh").status_code == 200  # old_cookie is now used up

    attacker = make_client()
    replay = attacker.post(f"{API}/auth/refresh", headers={"Cookie": f"refresh_token={old_cookie}"})
    assert replay.status_code == 401
    assert replay.json()["error_code"] == "REFRESH_TOKEN_REUSED"

    # The real owner's newest refresh token and access token no longer work either.
    assert client.post(f"{API}/auth/refresh").status_code == 401
    me = client.get(f"{API}/auth/me", headers=first["headers"])
    assert me.status_code == 401
    assert me.json()["error_code"] == "SESSION_REVOKED"


# ------------------------------------------------------------------ FR-AUTH-08


def test_logout_closes_the_session_on_the_server(client):
    """FR-AUTH-08: after logout the access token and the refresh token are dead."""
    user = new_user(client)
    assert client.post(f"{API}/auth/logout").status_code == 204
    me = client.get(f"{API}/auth/me", headers=user["headers"])
    assert me.status_code == 401
    assert me.json()["error_code"] == "SESSION_REVOKED"
    assert client.post(f"{API}/auth/refresh").status_code == 401


# ------------------------------------------------------------------ FR-AUTH-09


def test_sessions_list_and_revoke_other_device(client, make_client):
    """FR-AUTH-09"""
    username = make_user(client)
    laptop = login_ok(client, username)
    phone_client = make_client()
    phone = login_ok(phone_client, username)

    sessions = client.get(f"{API}/auth/sessions", headers=laptop["headers"]).json()
    assert len(sessions) == 2
    assert sum(1 for s in sessions if s["current"]) == 1

    other = next(s for s in sessions if not s["current"])
    assert client.delete(f"{API}/auth/sessions/{other['id']}", headers=laptop["headers"]).status_code == 204
    assert phone_client.get(f"{API}/auth/me", headers=phone["headers"]).status_code == 401
    assert client.get(f"{API}/auth/me", headers=laptop["headers"]).status_code == 200


def test_cannot_revoke_someone_elses_session(client, make_client):
    """FR-AUTH-09: another user's session is simply not found (404)."""
    owner = new_user(client)
    sessions = client.get(f"{API}/auth/sessions", headers=owner["headers"]).json()
    stranger_client = make_client()
    stranger = new_user(stranger_client)
    response = stranger_client.delete(f"{API}/auth/sessions/{sessions[0]['id']}", headers=stranger["headers"])
    assert response.status_code == 404


# ------------------------------------------------------------------ FR-AUTH-10


def test_profile_update(client):
    """FR-AUTH-10"""
    user = new_user(client)
    response = client.patch(f"{API}/auth/me", json={"full_name": "New Name"}, headers=user["headers"])
    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


# ------------------------------------------------------------------ FR-AUTH-11


def test_change_password_needs_current_password(client):
    """FR-AUTH-11"""
    user = new_user(client)
    response = client.post(
        f"{API}/auth/change-password",
        json={"current_password": "Wrong12345", "new_password": "Newpass456"},
        headers=user["headers"],
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "WRONG_PASSWORD"


def test_change_password_signs_out_other_devices(client, make_client):
    """FR-AUTH-11"""
    username = make_user(client)
    laptop = login_ok(client, username)
    phone_client = make_client()
    phone = login_ok(phone_client, username)
    response = client.post(
        f"{API}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "Newpass456"},
        headers=laptop["headers"],
    )
    assert response.status_code == 204
    assert phone_client.get(f"{API}/auth/me", headers=phone["headers"]).status_code == 401
    assert client.get(f"{API}/auth/me", headers=laptop["headers"]).status_code == 200
    assert login(client, username, "Newpass456").status_code == 200


# ------------------------------------------------------------------ FR-AUTH-12


def test_missing_token_is_401(client):
    """FR-AUTH-12"""
    response = client.get(f"{API}/auth/me")
    assert response.status_code == 401
    assert response.json()["error_code"] == "NOT_AUTHENTICATED"


def test_garbage_token_is_401(client):
    """FR-AUTH-12"""
    response = client.get(f"{API}/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "TOKEN_INVALID"


def test_tampered_token_is_rejected(client):
    """FR-AUTH-12: the payload says admin, but the signature no longer matches."""
    user = new_user(client)
    header, payload, signature = user["token"].split(".")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    claims["role"] = "admin"
    forged = f"{header}.{_b64(claims)}.{signature}"
    response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "TOKEN_INVALID"


def test_expired_token_is_401(client):
    """FR-AUTH-12"""
    user = new_user(client)
    claims = jwt.decode(user["token"], config.JWT_SECRET, algorithms=["HS256"])
    claims["exp"] = int(time.time()) - 10
    expired = jwt.encode(claims, config.JWT_SECRET, algorithm="HS256")
    response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "TOKEN_EXPIRED"


def test_token_signed_with_another_algorithm_is_rejected(client):
    """FR-AUTH-12: only HS256 is accepted (no 'none' algorithm trick)."""
    user = new_user(client)
    claims = jwt.decode(user["token"], config.JWT_SECRET, algorithms=["HS256"])
    forged = jwt.encode(claims, "", algorithm="none")
    response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401
