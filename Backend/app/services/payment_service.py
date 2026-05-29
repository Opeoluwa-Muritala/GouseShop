from datetime import datetime, timezone
import hashlib
import hmac
from time import monotonic
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from json import JSONDecodeError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import OrderStatus, PaymentProvider, PaymentStatus
from app.models.order import Order
from app.models.payment import Payment


SUPPORTED_PAYSTACK_COUNTRIES = {"NG", "GH", "ZA", "KE"}
PAYSTACK_BASE_URL = "https://api.paystack.co"
FLUTTERWAVE_BASE_URL = "https://api.flutterwave.com/v3"
FLUTTERWAVE_TOKEN_URL = "https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token"
class ExpiringTokenCache:
    def __init__(self) -> None:
        self.token: str | None = None
        self.expires_at = 0.0

    def get(self) -> str | None:
        if self.token and monotonic() < self.expires_at - 60:
            return self.token
        return None

    def set(self, token: str, expires_in: int) -> None:
        self.token = token
        self.expires_at = monotonic() + expires_in

    def clear(self) -> None:
        self.token = None
        self.expires_at = 0.0


flutterwave_token_cache = ExpiringTokenCache()


def _provider_response_json(response: httpx.Response, provider: str) -> dict:
    try:
        data = response.json()
    except JSONDecodeError:
        response_preview = response.text[:300].strip()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": provider,
                "message": "Provider returned a non-JSON response",
                "status_code": response.status_code,
                "response_preview": response_preview,
            },
        )
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": provider,
                "message": "Provider returned an unexpected response",
                "status_code": response.status_code,
            },
        )
    return data


def choose_provider(provider: str | None = None, country: str | None = None) -> PaymentProvider:
    if provider:
        return PaymentProvider(provider)
    if country and country.upper() in SUPPORTED_PAYSTACK_COUNTRIES:
        return PaymentProvider.PAYSTACK
    return PaymentProvider.FLUTTERWAVE


async def initiate_payment(
    session: AsyncSession, order: Order, provider: str | None = None, country: str | None = None, currency: str | None = None
) -> Payment:
    selected = choose_provider(provider, country)
    reference = f"{selected.value}_{uuid4().hex}"
    amount = order.total
    selected_currency = (currency or order.currency or "NGN").upper()
    if selected == PaymentProvider.PAYSTACK and selected_currency not in {"NGN", "GHS", "ZAR", "KES"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Paystack does not support {selected_currency} for this checkout",
        )
    order.currency = selected_currency

    if settings.use_fake_external_services:
        checkout_url = f"https://checkout.gouseshop.local/{reference}"
        provider_response = {"mode": "fake", "reference": reference}
    elif selected == PaymentProvider.PAYSTACK:
        checkout_url, provider_response = await _initiate_paystack_payment(order, reference, amount, selected_currency)
    elif selected == PaymentProvider.FLUTTERWAVE:
        checkout_url, provider_response = await _initiate_flutterwave_payment(order, reference, amount, selected_currency)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment provider")

    payment = Payment(
        order_id=order.id,
        provider=selected,
        provider_reference=reference,
        provider_checkout_url=checkout_url,
        amount=amount,
        currency=selected_currency,
        status=PaymentStatus.INITIALIZED,
        provider_response=provider_response,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment_by_reference(session: AsyncSession, reference: str) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.provider_reference == reference))
    return result.scalar_one_or_none()


async def verify_payment(session: AsyncSession, reference: str) -> Payment | None:
    payment = await get_payment_by_reference(session, reference)
    if payment is None:
        return None

    if settings.use_fake_external_services:
        verified = True
        provider_response = {**(payment.provider_response or {}), "verified": True}
    elif payment.provider == PaymentProvider.PAYSTACK:
        verified, provider_response = await _verify_paystack_payment(payment)
    elif payment.provider == PaymentProvider.FLUTTERWAVE:
        verified, provider_response = await _verify_flutterwave_payment(payment)
    else:
        verified = False
        provider_response = payment.provider_response or {}

    payment.provider_response = provider_response
    if not verified:
        payment.status = PaymentStatus.FAILED
        await session.commit()
        await session.refresh(payment)
        return payment

    payment.status = PaymentStatus.PAID
    payment.verified_at = datetime.now(timezone.utc)
    order = await session.get(Order, payment.order_id)
    if order:
        order.status = OrderStatus.PAID
        order.paid_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(payment)
    return payment


async def apply_webhook_payment_update(
    session: AsyncSession, provider: PaymentProvider, payload: dict
) -> Payment | None:
    reference: str | None = None
    status_value: str | None = None
    amount: int | None = None
    currency: str | None = None

    if provider == PaymentProvider.PAYSTACK:
        data = payload.get("data") or {}
        reference = data.get("reference")
        status_value = data.get("status")
        amount = int(data.get("amount") or 0) // 100
        currency = str(data.get("currency") or "").upper()
    elif provider == PaymentProvider.FLUTTERWAVE:
        data = payload.get("data") or {}
        reference = data.get("tx_ref")
        status_value = data.get("status")
        amount = int(float(data.get("amount") or 0))
        currency = str(data.get("currency") or "").upper()

    if not reference:
        return None
    payment = await get_payment_by_reference(session, reference)
    if payment is None or payment.provider != provider:
        return None

    provider_response = {**(payment.provider_response or {}), "webhook": payload}
    payment.provider_response = provider_response
    successful = status_value in {"success", "successful"} and amount == payment.amount and currency == payment.currency.upper()
    if not successful:
        payment.status = PaymentStatus.FAILED
        await session.commit()
        await session.refresh(payment)
        return payment

    payment.status = PaymentStatus.PAID
    payment.verified_at = datetime.now(timezone.utc)
    order = await session.get(Order, payment.order_id)
    if order:
        order.status = OrderStatus.PAID
        order.paid_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(payment)
    return payment


async def refund_payment(session: AsyncSession, reference: str, amount: int | None = None) -> Payment | None:
    payment = await get_payment_by_reference(session, reference)
    if payment is None:
        return None
    refund_amount = amount or payment.amount
    if settings.use_fake_external_services or payment.provider == PaymentProvider.FAKE:
        provider_response = {**(payment.provider_response or {}), "refund": {"mode": "fake", "amount": refund_amount}}
    elif payment.provider == PaymentProvider.PAYSTACK:
        provider_response = await _refund_paystack_payment(payment, refund_amount)
    elif payment.provider == PaymentProvider.FLUTTERWAVE:
        provider_response = await _refund_flutterwave_payment(payment, refund_amount)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment provider")
    payment.status = PaymentStatus.REFUNDED
    payment.provider_response = provider_response
    order = await session.get(Order, payment.order_id)
    if order:
        order.status = OrderStatus.REFUNDED
    await session.commit()
    await session.refresh(payment)
    return payment


def verify_webhook_signature(provider: PaymentProvider, payload: bytes, signature: str | None) -> bool:
    if provider == PaymentProvider.FAKE:
        return True
    if not signature:
        return False
    if provider == PaymentProvider.PAYSTACK:
        secret = settings.paystack_webhook_secret or settings.paystack_secret_key
        if not secret:
            return False
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha512).hexdigest()
        return hmac.compare_digest(digest, signature)
    if provider == PaymentProvider.FLUTTERWAVE:
        secret = settings.flutterwave_webhook_secret
        return bool(secret) and hmac.compare_digest(secret, signature)
    return False


def _customer_email(order: Order) -> str:
    if order.user and order.user.email:
        return order.user.email
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order customer email is required")


def _provider_not_configured(provider: PaymentProvider) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{provider.value} is not configured",
    )


def _flutterwave_client_credentials() -> tuple[str | None, str | None]:
    return (
        settings.flutterwave_client_id or settings.flw_client_id,
        settings.flutterwave_client_secret or settings.flw_client_secret,
    )


async def _get_flutterwave_access_token() -> str:
    cached_token = flutterwave_token_cache.get()
    if cached_token:
        return cached_token

    client_id, client_secret = _flutterwave_client_credentials()
    if not client_id or not client_secret:
        if settings.flutterwave_secret_key:
            return settings.flutterwave_secret_key
        raise _provider_not_configured(PaymentProvider.FLUTTERWAVE)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            FLUTTERWAVE_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        )
    data = _provider_response_json(response, "flutterwave")
    access_token = data.get("access_token")
    if response.status_code >= 400 or not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": "flutterwave",
                "message": data.get("error_description") or data.get("error") or "Unable to generate access token",
                "status_code": response.status_code,
                "response": data,
            },
        )

    expires_in = int(data.get("expires_in") or 600)
    flutterwave_token_cache.set(access_token, expires_in)
    return access_token


async def _initiate_paystack_payment(
    order: Order, reference: str, amount: int, currency: str
) -> tuple[str, dict]:
    if not settings.paystack_secret_key:
        raise _provider_not_configured(PaymentProvider.PAYSTACK)

    payload = {
        "email": _customer_email(order),
        "amount": amount * 100,
        "currency": currency,
        "reference": reference,
        "callback_url": settings.payment_callback_url,
        "metadata": {"order_id": order.id},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{PAYSTACK_BASE_URL}/transaction/initialize",
            headers={
                "Authorization": f"Bearer {settings.paystack_secret_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "GouseShop/1.0",
            },
            json=payload,
        )
    data = _provider_response_json(response, "paystack")
    if response.status_code >= 400 or not data.get("status"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": "paystack",
                "message": data.get("message", "Payment initialization failed"),
                "status_code": response.status_code,
                "response": data,
            },
        )
    checkout_url = data["data"]["authorization_url"]
    return checkout_url, {"provider": "paystack", "initialize": data}


async def _initiate_flutterwave_payment(
    order: Order, reference: str, amount: int, currency: str
) -> tuple[str, dict]:
    access_token = await _get_flutterwave_access_token()

    payload = {
        "tx_ref": reference,
        "amount": amount,
        "currency": currency,
        "redirect_url": settings.payment_callback_url,
        "customer": {"email": _customer_email(order)},
        "customizations": {"title": settings.app_name, "description": f"Order #{order.id}"},
        "meta": {"order_id": order.id},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{FLUTTERWAVE_BASE_URL}/payments",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "GouseShop/1.0",
            },
            json=payload,
        )
    data = _provider_response_json(response, "flutterwave")
    if response.status_code >= 400 or data.get("status") != "success":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": "flutterwave",
                "message": data.get("message", "Payment initialization failed"),
                "status_code": response.status_code,
                "response": data,
            },
        )
    checkout_url = (data.get("data") or {}).get("link")
    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"provider": "flutterwave", "message": "Flutterwave did not return a checkout link", "response": data},
        )
    return checkout_url, {"provider": "flutterwave", "initialize": data}


async def _verify_paystack_payment(payment: Payment) -> tuple[bool, dict]:
    if not settings.paystack_secret_key:
        raise _provider_not_configured(PaymentProvider.PAYSTACK)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{PAYSTACK_BASE_URL}/transaction/verify/{payment.provider_reference}",
            headers={
                "Authorization": f"Bearer {settings.paystack_secret_key}",
                "Accept": "application/json",
                "User-Agent": "GouseShop/1.0",
            },
        )
    data = _provider_response_json(response, "paystack")
    provider_response = {**(payment.provider_response or {}), "verify": data}
    transaction = data.get("data") or {}
    verified = (
        response.status_code < 400
        and data.get("status") is True
        and transaction.get("status") == "success"
        and transaction.get("reference") == payment.provider_reference
        and int(transaction.get("amount") or 0) == payment.amount * 100
        and str(transaction.get("currency") or "").upper() == payment.currency.upper()
    )
    return verified, provider_response


async def _verify_flutterwave_payment(payment: Payment) -> tuple[bool, dict]:
    access_token = await _get_flutterwave_access_token()

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{FLUTTERWAVE_BASE_URL}/transactions/verify_by_reference",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "GouseShop/1.0",
            },
            params={"tx_ref": payment.provider_reference},
        )
    data = _provider_response_json(response, "flutterwave")
    provider_response = {**(payment.provider_response or {}), "verify": data}
    transaction = data.get("data") or {}
    verified = (
        response.status_code < 400
        and data.get("status") == "success"
        and transaction.get("status") == "successful"
        and transaction.get("tx_ref") == payment.provider_reference
        and int(float(transaction.get("amount") or 0)) == payment.amount
        and str(transaction.get("currency") or "").upper() == payment.currency.upper()
    )
    return verified, provider_response


async def _refund_paystack_payment(payment: Payment, amount: int) -> dict:
    if not settings.paystack_secret_key:
        raise _provider_not_configured(PaymentProvider.PAYSTACK)

    payload = {"transaction": payment.provider_reference, "amount": amount * 100}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{PAYSTACK_BASE_URL}/refund",
            headers={
                "Authorization": f"Bearer {settings.paystack_secret_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "GouseShop/1.0",
            },
            json=payload,
        )
    data = _provider_response_json(response, "paystack")
    if response.status_code >= 400 or data.get("status") is not True:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": "paystack",
                "message": data.get("message", "Refund failed"),
                "status_code": response.status_code,
                "response": data,
            },
        )
    return {**(payment.provider_response or {}), "refund": data}


async def _refund_flutterwave_payment(payment: Payment, amount: int) -> dict:
    access_token = await _get_flutterwave_access_token()
    transaction_id = _flutterwave_transaction_id(payment)
    if transaction_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flutterwave transaction id is required before refunding",
        )

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{FLUTTERWAVE_BASE_URL}/transactions/{transaction_id}/refund",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "GouseShop/1.0",
            },
            json={"amount": amount},
        )
    data = _provider_response_json(response, "flutterwave")
    if response.status_code >= 400 or data.get("status") != "success":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "provider": "flutterwave",
                "message": data.get("message", "Refund failed"),
                "status_code": response.status_code,
                "response": data,
            },
        )
    return {**(payment.provider_response or {}), "refund": data}


def _flutterwave_transaction_id(payment: Payment) -> int | str | None:
    response = payment.provider_response or {}
    for section in ("verify", "initialize"):
        data = response.get(section)
        if isinstance(data, dict):
            transaction = data.get("data") or {}
            if isinstance(transaction, dict) and transaction.get("id") is not None:
                return transaction["id"]
    return None
