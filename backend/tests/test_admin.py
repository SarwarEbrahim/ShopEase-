"""Admin dashboard endpoints."""

from tests.helpers import API, admin_login, new_user, PRODUCT


def test_stats_and_user_search(client):
    """FR-ADM-01, FR-ADM-02"""
    admin = admin_login(client)
    stats = client.get(f"{API}/admin/stats", headers=admin["headers"]).json()
    assert stats["total_users"] >= 5 and stats["admins"] >= 2
    found = client.get(f"{API}/admin/users?q=user1&role=user", headers=admin["headers"]).json()
    assert found["total"] >= 1
    assert all(u["role"] == "user" for u in found["items"])


def test_user_overview_shows_sessions_and_activity(client, make_client):
    """FR-ADM-03"""
    user_client = make_client()
    user = new_user(user_client)
    admin = admin_login(client)
    overview = client.get(f"{API}/admin/users/{user['id']}/overview", headers=admin["headers"])
    assert overview.status_code == 200
    body = overview.json()
    assert body["user"]["username"] == user["username"]
    assert len(body["sessions"]) == 1
    assert any(item["event"] == "login" for item in body["recent_activity"])


def test_admin_can_revoke_all_sessions_of_a_user(client, make_client):
    """FR-ADM-06"""
    user_client = make_client()
    user = new_user(user_client)
    admin = admin_login(client)
    result = client.post(f"{API}/admin/users/{user['id']}/revoke-sessions", headers=admin["headers"])
    assert result.status_code == 200 and result.json()["updated"] == 1
    assert user_client.get(f"{API}/auth/me", headers=user["headers"]).status_code == 401


def test_bulk_ban_skips_admins_and_reports_counts(client, make_client):
    """FR-ADM-07"""
    victim = new_user(make_client())
    admin = admin_login(client)
    other_admin = client.get(f"{API}/admin/users?q=admin2", headers=admin["headers"]).json()["items"][0]
    result = client.post(
        f"{API}/admin/users/bulk-ban",
        json={"ids": [victim["id"], other_admin["id"]], "reason": "test"},
        headers=admin["headers"],
    ).json()
    assert result == {"updated": 1, "skipped": 1}
    client.post(f"{API}/admin/users/bulk-unban", json={"ids": [victim["id"]]}, headers=admin["headers"])


def test_admin_can_delete_a_product(client, make_client):
    """FR-ADM-08"""
    owner_client = make_client()
    owner = new_user(owner_client)
    product_id = owner_client.post(f"{API}/products", json=PRODUCT, headers=owner["headers"]).json()["id"]
    admin = admin_login(client)
    assert client.delete(f"{API}/admin/products/{product_id}", headers=admin["headers"]).status_code == 204
    assert owner_client.get(f"{API}/products/{product_id}", headers=owner["headers"]).status_code == 404


def test_activity_log_records_login_and_failed_login(client):
    """FR-ADM-09"""
    from tests.helpers import login, make_user

    username = make_user(client)
    login(client, username, "Wrong12345")
    login(client, username)
    admin = admin_login(client)
    log = client.get(f"{API}/admin/audit?q={username}&page_size=50", headers=admin["headers"]).json()
    events = {item["event"] for item in log["items"]}
    assert {"login", "login_failed"} <= events


def test_security_view_counts_failed_logins(client):
    """FR-ADM-10"""
    from tests.helpers import login, make_user

    username = make_user(client)
    for _ in range(3):
        login(client, username, "Wrong12345")
    admin = admin_login(client)
    view = client.get(f"{API}/admin/security", headers=admin["headers"]).json()
    assert any(item["key"] == username for item in view["by_account"])


def test_csv_export_is_a_download_and_guards_formulas(client):
    """FR-ADM-11"""
    admin = admin_login(client)
    response = client.get(f"{API}/admin/export/users.csv", headers=admin["headers"])
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "username" in response.text.splitlines()[0]

    from features.admin.exports import csv_safe

    assert csv_safe("=1+1").startswith("'")
