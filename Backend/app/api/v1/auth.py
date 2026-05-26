from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.rate_limit import rate_limit
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import ForgotPasswordRequest, ResetPasswordRequest, UserCreate, UserRead
from app.services.cart_service import merge_guest_cart_into_user_cart
from app.services.auth_service import (
    authenticate_user,
    build_password_reset_token,
    build_tokens,
    create_user,
    decode_user_id,
    get_user_by_email,
    is_refresh_token_revoked,
    revoke_refresh_token,
    reset_password,
)

router = APIRouter()


class LoginRequest(UserCreate):
    pass


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=Token, dependencies=[Depends(rate_limit("auth_register", 10, 60))])
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    existing = await session.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = await create_user(session, data)
    if x_session_id:
        await merge_guest_cart_into_user_cart(session, x_session_id, user.id)
    return build_tokens(user)


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit("auth_login", 10, 60))])
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    user = await authenticate_user(session, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if x_session_id:
        await merge_guest_cart_into_user_cart(session, x_session_id, user.id)
    return build_tokens(user)


@router.post("/refresh", response_model=Token)
async def refresh(refresh_request: RefreshRequest):
    if await is_refresh_token_revoked(refresh_request.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    user_id = decode_user_id(refresh_request.refresh_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return build_tokens(type("UserStub", (), {"id": int(user_id)}))


@router.post("/logout")
async def logout(logout_request: LogoutRequest):
    await revoke_refresh_token(logout_request.refresh_token)
    return {"detail": "Logged out"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(session, data.email)
    if not user:
        return {"detail": "If the email exists, a reset link will be sent"}
    token = build_password_reset_token(user)
    return {"detail": "If the email exists, a reset link will be sent", "reset_token": token}


@router.post("/reset-password")
async def reset_password_endpoint(data: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    if not await reset_password(session, data.token, data.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    return {"detail": "Password reset successful"}
