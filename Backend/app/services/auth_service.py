from typing import Optional
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    user = User(email=data.email, password_hash=hash_password(data.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def build_tokens(user: User) -> dict:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def revoke_refresh_token(token: str) -> None:
    key = f"refresh:{sha256(token.encode('utf-8')).hexdigest()}"
    await redis_client.set(key, "revoked", ex=60 * 60 * 24 * 30)


async def is_refresh_token_revoked(token: str) -> bool:
    if token is None:
        return True
    key = f"refresh:{sha256(token.encode('utf-8')).hexdigest()}"
    return await redis_client.exists(key) == 1


def decode_user_id(token: str) -> Optional[str]:
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("sub")


def build_password_reset_token(user: User) -> str:
    return create_password_reset_token(str(user.id))


async def reset_password(session: AsyncSession, token: str, password: str) -> bool:
    payload = decode_token(token)
    if not payload or payload.get("type") != "password_reset":
        return False
    user_id = payload.get("sub")
    if not user_id:
        return False
    user = await session.get(User, int(user_id))
    if user is None:
        return False
    user.password_hash = hash_password(password)
    await session.commit()
    return True
