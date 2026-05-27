import asyncio

import pytest
from sqlalchemy import select

from app.core.database import async_session
from app.core.security import create_refresh_token
from app.models.email import EmailLog
from app.models.user import User
from app.services.auth_service import build_email_verification_token

pytestmark = pytest.mark.db


async def _user_by_email(email: str) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one()


async def _set_user_flags(email: str, *, verified: bool | None = None, active: bool | None = None) -> None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        if verified is not None:
            user.is_email_verified = verified
        if active is not None:
            user.is_active = active
        await session.commit()


async def _email_count(email: str) -> int:
    async with async_session() as session:
        result = await session.execute(select(EmailLog).where(EmailLog.recipient == email))
        return len(result.scalars().all())


def test_auth_security_flows(client):
    weak = client.post("/api/v1/auth/register", json={"email": "weak@example.com", "password": "password"})
    assert weak.status_code == 422

    register = client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "secret123"})
    assert register.status_code == 200
    assert register.json()["access_token"]

    blocked_login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"})
    assert blocked_login.status_code == 403

    reset = client.post("/api/v1/auth/forgot-password", json={"email": "user@example.com"})
    assert reset.status_code == 200
    assert "reset_token" not in reset.json()
    assert asyncio.run(_email_count("user@example.com")) == 2

    access_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": register.json()["access_token"]})
    assert access_refresh.status_code == 401

    missing_user_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": create_refresh_token("999")})
    assert missing_user_refresh.status_code == 401

    asyncio.run(_set_user_flags("user@example.com", verified=True))
    login = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "secret123"})
    assert login.status_code == 200
    tokens = login.json()

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200

    asyncio.run(_set_user_flags("user@example.com", active=False))
    inactive_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert inactive_refresh.status_code == 401

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout.status_code == 200
    revoked_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert revoked_refresh.status_code == 401

    register = client.post("/api/v1/auth/register", json={"email": "verify@example.com", "password": "secret123"})
    assert register.status_code == 200

    user = asyncio.run(_user_by_email("verify@example.com"))
    token = build_email_verification_token(user)
    verify = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify.status_code == 200

    login = client.post("/api/v1/auth/login", json={"email": "verify@example.com", "password": "secret123"})
    assert login.status_code == 200
