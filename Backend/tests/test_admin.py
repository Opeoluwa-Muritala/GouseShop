import asyncio

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.user import User

pytestmark = pytest.mark.db


def _csrf_headers(client) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("gouseshop_csrf")}


async def _set_user_role(email: str, role: str) -> None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = role
        await session.commit()


def test_admin_current_user_and_product_delete(client):
    register = client.post("/api/v1/auth/register", json={"email": "admin@example.com", "password": "secret123"})
    assert register.status_code == 200

    asyncio.run(_set_user_role("admin@example.com", "admin"))

    login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "secret123"})
    assert login.status_code == 403

    # Verify before login
    from app.services.auth_service import build_email_verification_token

    async def verify_and_login():
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == "admin@example.com"))
            user = result.scalar_one()
            token = build_email_verification_token(user)
        return token

    token = asyncio.run(verify_and_login())
    verify = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify.status_code == 200

    login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "secret123"})
    assert login.status_code == 200
    auth_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"
    assert me.json()["role"] == "admin"

    product = client.post(
        "/api/v1/products/admin",
        json={"name": "Admin Test Product", "slug": "admin-test-product", "price": 999},
        headers=headers,
    )
    assert product.status_code == 200
    assert product.json()["slug"] == "admin-test-product"

    invalid_image = client.post(
        "/api/v1/products/admin/admin-test-product/images",
        files={"file": ("bad.png", b"not-a-real-png", "image/png")},
        headers=headers,
    )
    assert invalid_image.status_code == 400

    delete = client.delete("/api/v1/products/admin/admin-test-product", headers=headers)
    assert delete.status_code == 204

    missing = client.get("/api/v1/products/admin/admin-test-product", headers=headers)
    assert missing.status_code == 404


def test_admin_bootstrap_uses_environment_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_bootstrap_email", "bootstrap@example.com")
    monkeypatch.setattr(settings, "admin_bootstrap_password", "secret123")

    default_login = client.post("/admin/login", json={"email": "muritalaopeoluwa10@gmail.com", "password": "Iamanadmin"})
    assert default_login.status_code == 401

    bootstrap = client.post("/admin/login", json={"email": "bootstrap@example.com", "password": "secret123"})
    assert bootstrap.status_code == 200

    created = client.post(
        "/admin/users",
        json={"email": "next-admin@example.com", "password": "secret123"},
        headers=_csrf_headers(client),
    )
    assert created.status_code == 200
    assert created.json()["role"] == "admin"
