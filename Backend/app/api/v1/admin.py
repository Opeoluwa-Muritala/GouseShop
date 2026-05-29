from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_admin
from app.core.config import settings
from app.core.database import get_session
from app.core.rate_limit import rate_limit
from app.core.security import hash_password, set_auth_cookies
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import authenticate_user, build_tokens, get_user_by_email

router = APIRouter()


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminCreateRequest(BaseModel):
    email: EmailStr
    password: str


def _validate_admin_password(password: str) -> str:
    try:
        return UserCreate.validate_password(password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit("admin_login", 5, 60))])
async def admin_login(data: AdminLoginRequest, response: Response, session: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(session, data.email)
    if user is None:
        if (
            not settings.admin_bootstrap_email
            or not settings.admin_bootstrap_password
            or data.email != settings.admin_bootstrap_email
            or data.password != settings.admin_bootstrap_password
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")
        _validate_admin_password(data.password)
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            role=UserRole.ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        tokens = build_tokens(user)
        set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
        return tokens

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    authenticated = await authenticate_user(session, data.email, data.password)
    if not authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")
    tokens = build_tokens(user)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return tokens


@router.post("/users", response_model=UserRead, dependencies=[Depends(require_admin)])
async def create_admin_user(
    data: AdminCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not settings.admin_bootstrap_email or current_user.email != settings.admin_bootstrap_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the bootstrap admin can add more admins")
    _validate_admin_password(data.password)
    existing = await get_user_by_email(session, data.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.ADMIN,
        is_active=True,
        is_email_verified=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
