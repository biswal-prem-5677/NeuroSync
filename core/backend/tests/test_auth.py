"""
NeuroSync — Tests for Auth & Rate Limiting.
"""
import pytest


def test_magic_link_flow(client):
    # 1. Request magic link
    res = client.post("/api/v1/auth/magic-link", json={"email": "user@example.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    token = data["token"]

    # 2. Verify magic link token
    v_res = client.post("/api/v1/auth/verify", json={"token": token})
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["status"] == "authenticated"
    access_token = v_data["access_token"]
    assert access_token is not None

    # 3. Access profile via Bearer token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "user@example.com"


def test_auth_invalid_token(client):
    res = client.post("/api/v1/auth/verify", json={"token": "invalid-token"})
    assert res.status_code == 400


def test_auth_me_unauthorized(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
