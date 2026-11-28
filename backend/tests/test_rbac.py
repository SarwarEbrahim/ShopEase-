"""Authorisation: roles, ownership, group permissions, admin rules, banned users."""

from tests.helpers import API, PASSWORD, PRODUCT, admin_login, login, new_user


# ------------------------------------------------------------------ FR-RBAC-01


def test_normal_user_cannot_use_admin_endpoints(client):
    """FR-RBAC-01"""
    user = new_user(client)
    for path in ("/admin/users", "/admin/stats", "/admin/audit", "/admin/security"):
        response = client.get(f"{API}{path}", headers=user["headers"])
        assert response.status_code == 403, path
        assert response.json()["error_code"] == "FORBIDDEN"


def test_admin_can_use_admin_endpoints(client):
    """FR-RBAC-01"""
    admin = admin_login(client)
    assert client.get(f"{API}/admin/users", headers=admin["headers"]).status_code == 200
    assert client.get(f"{API}/admin/stats", headers=admin["headers"]).status_code == 200


def test_admin_endpoint_without_token_is_401(client):
    """FR-RBAC-01"""
    assert client.get(f"{API}/admin/users").status_code == 401


# ------------------------------------------------------------------ FR-RBAC-02


def test_user_sees_only_own_products(client, make_client):
    """FR-RBAC-02: ownership is applied in the query, not only checked afterwards."""
    alice = new_user(client)
    bob_client = make_client()
    bob = new_user(bob_client)
    created = client.post(f"{API}/products", json=PRODUCT, headers=alice["headers"])
    assert created.status_code == 201
    listing = bob_client.get(f"{API}/products", headers=bob["headers"]).json()
    assert listing["total"] == 0
    assert client.get(f"{API}/products", headers=alice["headers"]).json()["total"] == 1


def test_user_cannot_read_change_or_delete_another_users_product(client, make_client):
    """FR-RBAC-02"""
    alice = new_user(client)
    bob_client = make_client()
    bob = new_user(bob_client)
    product_id = client.post(f"{API}/products", json=PRODUCT, headers=alice["headers"]).json()["id"]
    url = f"{API}/products/{product_id}"
    assert bob_client.get(url, headers=bob["headers"]).status_code == 403
    assert bob_client.put(url, json=PRODUCT, headers=bob["headers"]).status_code == 403
    assert bob_client.delete(url, headers=bob["headers"]).status_code == 403
    assert client.get(url, headers=alice["headers"]).status_code == 200  # still there


def test_admin_can_read_any_product(client, make_client):
    """FR-RBAC-02"""
    alice = new_user(client)
    product_id = client.post(f"{API}/products", json=PRODUCT, headers=alice["headers"]).json()["id"]
    admin_client = make_client()
    admin = admin_login(admin_client)
    assert admin_client.get(f"{API}/products/{product_id}", headers=admin["headers"]).status_code == 200


# ------------------------------------------------------------------ FR-RBAC-03/04


def _group_with_members(client, make_client):
    """An owner, a member with create+edit, a member with assign only, and an outsider."""
    owner = new_user(client)
    editor_client, assigner_client, outsider_client = make_client(), make_client(), make_client()
    editor, assigner, outsider = new_user(editor_client), new_user(assigner_client), new_user(outsider_client)
    group_id = client.post(f"{API}/groups", json={"name": "Test Team"}, headers=owner["headers"]).json()["id"]
    base = f"{API}/groups/{group_id}"
    r = client.post(
        f"{base}/members",
        json={"username": editor["username"], "can_create": True, "can_edit": True},
        headers=owner["headers"],
    )
    assert r.status_code == 201, r.text
    r = client.post(
        f"{base}/members",
        json={"username": assigner["username"], "can_assign": True},
        headers=owner["headers"],
    )
    assert r.status_code == 201, r.text
    return {
        "base": base,
        "owner": owner,
        "editor": (editor_client, editor),
        "assigner": (assigner_client, assigner),
        "outsider": (outsider_client, outsider),
    }


def test_group_member_with_create_and_edit_can_add_and_change_products(client, make_client):
    """FR-RBAC-03"""
    g = _group_with_members(client, make_client)
    editor_client, editor = g["editor"]
    created = editor_client.post(f"{g['base']}/products", json=PRODUCT, headers=editor["headers"])
    assert created.status_code == 201, created.text
    product_id = created.json()["id"]
    updated = editor_client.put(
        f"{g['base']}/products/{product_id}", json={**PRODUCT, "name": "Renamed"}, headers=editor["headers"]
    )
    assert updated.status_code == 200


def test_group_member_without_permission_gets_403(client, make_client):
    """FR-RBAC-03: the assign-only member can neither create nor edit."""
    g = _group_with_members(client, make_client)
    assigner_client, assigner = g["assigner"]
    r = assigner_client.post(f"{g['base']}/products", json=PRODUCT, headers=assigner["headers"])
    assert r.status_code == 403


def test_group_assign_permission(client, make_client):
    """FR-RBAC-03: only members with assign (or the owner) can assign a product."""
    g = _group_with_members(client, make_client)
    editor_client, editor = g["editor"]
    assigner_client, assigner = g["assigner"]
    product_id = client.post(f"{g['base']}/products", json=PRODUCT, headers=g["owner"]["headers"]).json()["id"]
    url = f"{g['base']}/products/{product_id}/assign"
    assert editor_client.put(url, json={"user_id": assigner["id"]}, headers=editor["headers"]).status_code == 403
    assert assigner_client.put(url, json={"user_id": assigner["id"]}, headers=assigner["headers"]).status_code == 200


def test_outsider_cannot_see_the_group(client, make_client):
    """FR-RBAC-03"""
    g = _group_with_members(client, make_client)
    outsider_client, outsider = g["outsider"]
    assert outsider_client.get(g["base"], headers=outsider["headers"]).status_code == 403
    assert outsider_client.get(f"{g['base']}/products", headers=outsider["headers"]).status_code == 403


def test_only_the_owner_can_rename_delete_and_manage_members(client, make_client):
    """FR-RBAC-04"""
    g = _group_with_members(client, make_client)
    editor_client, editor = g["editor"]
    outsider_client, outsider = g["outsider"]
    product_id = client.post(f"{g['base']}/products", json=PRODUCT, headers=g["owner"]["headers"]).json()["id"]

    assert editor_client.patch(g["base"], json={"name": "Hacked"}, headers=editor["headers"]).status_code == 403
    assert editor_client.delete(g["base"], headers=editor["headers"]).status_code == 403
    assert editor_client.delete(f"{g['base']}/products/{product_id}", headers=editor["headers"]).status_code == 403
    add = editor_client.post(
        f"{g['base']}/members", json={"username": outsider["username"], "can_edit": True}, headers=editor["headers"]
    )
    assert add.status_code == 403

    # The owner can.
    assert client.patch(g["base"], json={"name": "Renamed"}, headers=g["owner"]["headers"]).status_code == 200
    assert client.delete(f"{g['base']}/products/{product_id}", headers=g["owner"]["headers"]).status_code == 204


# ------------------------------------------------------------------ FR-RBAC-05


def test_admin_cannot_change_own_role_or_ban_self_or_another_admin(client):
    """FR-RBAC-05"""
    admin = admin_login(client, "admin1")
    other_admin = client.get(f"{API}/admin/users?q=admin2", headers=admin["headers"]).json()["items"][0]

    own_role = client.patch(f"{API}/admin/users/{admin['id']}/role", json={"role": "user"}, headers=admin["headers"])
    assert own_role.status_code == 403
    assert own_role.json()["error_code"] == "CANNOT_MODIFY_SELF"

    ban_self = client.post(f"{API}/admin/users/{admin['id']}/ban", json={"reason": "x"}, headers=admin["headers"])
    assert ban_self.status_code == 403
    assert ban_self.json()["error_code"] == "CANNOT_MODIFY_SELF"

    ban_admin = client.post(f"{API}/admin/users/{other_admin['id']}/ban", json={"reason": "x"}, headers=admin["headers"])
    assert ban_admin.status_code == 403
    assert ban_admin.json()["error_code"] == "CANNOT_MODIFY_ADMIN"


# ------------------------------------------------------------------ FR-RBAC-06


def test_banned_user_is_rejected_on_the_next_request(client, make_client):
    """FR-RBAC-06 + FR-ADM-04: the old token stops working at once."""
    victim_client = make_client()
    victim = new_user(victim_client)
    assert victim_client.get(f"{API}/auth/me", headers=victim["headers"]).status_code == 200

    admin = admin_login(client)
    banned = client.post(f"{API}/admin/users/{victim['id']}/ban", json={"reason": "spam"}, headers=admin["headers"])
    assert banned.status_code == 200

    me = victim_client.get(f"{API}/auth/me", headers=victim["headers"])
    assert me.status_code == 403
    assert me.json()["error_code"] == "USER_BANNED"
    assert victim_client.post(f"{API}/auth/refresh").status_code == 401  # sessions were closed
    assert login(victim_client, victim["username"], PASSWORD).status_code == 403  # cannot log in

    client.post(f"{API}/admin/users/{victim['id']}/unban", headers=admin["headers"])
    assert login(victim_client, victim["username"], PASSWORD).status_code == 200
