def test_register_login_refresh_logout(client):
    register = client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "secret123"})
    assert register.status_code == 200
    assert register.json()["access_token"]

    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"})
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout.status_code == 200
