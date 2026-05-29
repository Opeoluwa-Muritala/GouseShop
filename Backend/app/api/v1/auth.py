from fastapi import APIRouter, Body, Cookie, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.core.security import REFRESH_COOKIE_NAME, clear_auth_cookies, decode_token, set_auth_cookies
from app.core.rate_limit import rate_limit
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import ForgotPasswordRequest, ResetPasswordRequest, UserCreate, UserRead, VerifyEmailRequest
from app.services.email_service import send_email
from app.services.cart_service import merge_guest_cart_into_user_cart
from app.services.auth_service import (
    authenticate_user,
    build_email_verification_token,
    build_password_reset_token,
    build_tokens,
    create_user,
    get_user_by_email,
    is_refresh_token_revoked,
    revoke_refresh_token,
    reset_password,
    verify_email_token,
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
    response: Response,
    session: AsyncSession = Depends(get_session),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    existing = await session.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = await create_user(session, data)
    verification_token = build_email_verification_token(user)
    await send_email(
        session,
        user.email,
        "Verify your GouseShop email",
        "email_verification",
        {"token": verification_token, "user_id": user.id},
    )
    if x_session_id:
        await merge_guest_cart_into_user_cart(session, x_session_id, user.id)
    tokens = build_tokens(user)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return tokens


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit("auth_login", 10, 60))])
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    user = await authenticate_user(session, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")
    if not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required")
    if x_session_id:
        await merge_guest_cart_into_user_cart(session, x_session_id, user.id)
    tokens = build_tokens(user)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return tokens


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=Token, dependencies=[Depends(rate_limit("auth_refresh", 30, 60))])
async def refresh(
    response: Response,
    refresh_request: RefreshRequest | None = Body(None),
    refresh_cookie: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
    session: AsyncSession = Depends(get_session),
):
    refresh_token = refresh_request.refresh_token if refresh_request else refresh_cookie
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if await is_refresh_token_revoked(refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = await session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    await revoke_refresh_token(refresh_token)
    tokens = build_tokens(user)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return tokens


@router.post("/logout", dependencies=[Depends(rate_limit("auth_logout", 30, 60))])
async def logout(
    response: Response,
    logout_request: LogoutRequest | None = Body(None),
    refresh_cookie: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
):
    refresh_token = logout_request.refresh_token if logout_request else refresh_cookie
    if refresh_token:
        await revoke_refresh_token(refresh_token)
    clear_auth_cookies(response)
    return {"detail": "Logged out"}


@router.post("/forgot-password", dependencies=[Depends(rate_limit("auth_forgot_password", 5, 60))])
async def forgot_password(data: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(session, data.email)
    if not user:
        return {"detail": "If the email exists, a reset link will be sent"}
    token = build_password_reset_token(user)
    await send_email(
        session,
        user.email,
        "Reset your GouseShop password",
        "password_reset",
        {"token": token, "user_id": user.id},
    )
    return {"detail": "If the email exists, a reset link will be sent"}


@router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest, session: AsyncSession = Depends(get_session)):
    if not await verify_email_token(session, data.token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
    return {"detail": "Email verified"}


@router.post("/resend-verification", dependencies=[Depends(rate_limit("auth_resend_verification", 5, 60))])
async def resend_verification(data: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(session, data.email)
    if user and user.is_active and not user.is_email_verified:
        token = build_email_verification_token(user)
        await send_email(
            session,
            user.email,
            "Verify your GouseShop email",
            "email_verification",
            {"token": token, "user_id": user.id},
        )
    return {"detail": "If the email exists, a verification link will be sent"}


@router.post("/reset-password", dependencies=[Depends(rate_limit("auth_reset_password", 5, 60))])
async def reset_password_endpoint(data: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    if not await reset_password(session, data.token, data.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    return {"detail": "Password reset successful"}
