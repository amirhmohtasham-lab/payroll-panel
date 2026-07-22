"""Auth flow: login, /api/me, logout, invalid credentials."""
from __future__ import annotations


def test_login_success(client, operator_user):
    res = client.post("/api/login", json={"username": "operator1", "password": "op-pass-123"})
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "operator"
    assert body["redirect"] == "/operator"
    assert "payroll_session" in res.cookies


def test_login_wrong_password(client, operator_user):
    res = client.post("/api/login", json={"username": "operator1", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post("/api/login", json={"username": "nobody", "password": "whatever"})
    assert res.status_code == 401


def test_me_requires_auth(client):
    res = client.get("/api/me")
    assert res.status_code == 401


def test_me_after_login(client, accountant_user):
    client.post("/api/login", json={"username": "admin1", "password": "acc-pass-123"})
    res = client.get("/api/me")
    assert res.status_code == 200
    assert res.json()["username"] == "admin1"
    assert res.json()["role"] == "accountant"


def test_logout_invalidates_session(client, operator_user):
    client.post("/api/login", json={"username": "operator1", "password": "op-pass-123"})
    assert client.get("/api/me").status_code == 200

    res = client.post("/api/logout")
    assert res.status_code == 200

    res2 = client.get("/api/me")
    assert res2.status_code == 401
