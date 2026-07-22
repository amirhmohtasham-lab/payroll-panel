"""Role-based access control: operator vs accountant endpoint guards."""
from __future__ import annotations


def test_operator_cannot_list_users(client, operator_user):
    client.post("/api/login", json={"username": "operator1", "password": "op-pass-123"})
    res = client.get("/api/users")
    assert res.status_code == 403


def test_accountant_can_list_users(client, accountant_user):
    client.post("/api/login", json={"username": "admin1", "password": "acc-pass-123"})
    res = client.get("/api/users")
    assert res.status_code == 200
    usernames = [u["username"] for u in res.json()]
    assert "admin1" in usernames


def test_operator_cannot_access_reports(client, operator_user):
    client.post("/api/login", json={"username": "operator1", "password": "op-pass-123"})
    res = client.get("/api/reports/data")
    assert res.status_code == 403


def test_accountant_can_access_months(client, accountant_user, operator_user):
    client.post("/api/login", json={"username": "admin1", "password": "acc-pass-123"})
    res = client.get("/api/months")
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_accountant_create_and_delete_user(client, accountant_user):
    client.post("/api/login", json={"username": "admin1", "password": "acc-pass-123"})
    res = client.post(
        "/api/users",
        json={"username": "newop", "password": "newpass123", "name": "New Op", "role": "operator"},
    )
    assert res.status_code == 201
    user_id = res.json()["id"]

    res2 = client.delete(f"/api/users/{user_id}")
    assert res2.status_code == 204

    res3 = client.get("/api/users")
    usernames = [u["username"] for u in res3.json()]
    assert "newop" not in usernames


def test_operator_cannot_create_user(client, operator_user):
    client.post("/api/login", json={"username": "operator1", "password": "op-pass-123"})
    res = client.post(
        "/api/users",
        json={"username": "x", "password": "somepass123", "name": "X", "role": "operator"},
    )
    assert res.status_code == 403
