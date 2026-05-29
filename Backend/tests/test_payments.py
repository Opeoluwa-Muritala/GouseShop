import asyncio
import hashlib
import hmac

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.database import async_session
from app.models.enums import OrderStatus, PaymentProvider, PaymentStatus
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.services.auth_service import build_tokens
from app.services import payment_service
from app.services.payment_service import get_payment_by_reference, refund_payment, verify_webhook_signature

pytestmark = pytest.mark.db


async def _create_paid_payment(reference: str) -> None:
    async with async_session() as session:
        order = Order(user_id=None, total=5000, currency="NGN", status=OrderStatus.PAID)
        session.add(order)
        await session.flush()
        session.add(
            Payment(
                order_id=order.id,
                provider=PaymentProvider.PAYSTACK,
                provider_reference=reference,
                amount=5000,
                currency="NGN",
                status=PaymentStatus.PAID,
                provider_response={},
            )
        )
        await session.commit()


async def _create_user_payment_fixture():
    async with async_session() as session:
        owner = User(email="pay-owner@example.com", password_hash="hash", is_email_verified=True)
        other = User(email="pay-other@example.com", password_hash="hash", is_email_verified=True)
        session.add_all([owner, other])
        await session.flush()
        order = Order(user_id=owner.id, total=5000, currency="NGN", status=OrderStatus.PENDING_PAYMENT)
        session.add(order)
        await session.flush()
        payment = Payment(
            order_id=order.id,
            provider=PaymentProvider.PAYSTACK,
            provider_reference="owner_ref",
            provider_checkout_url="https://checkout.example/owner_ref",
            amount=5000,
            currency="NGN",
            status=PaymentStatus.INITIALIZED,
            provider_response={"secret": "provider-payload"},
        )
        session.add(payment)
        await session.commit()
        return build_tokens(owner)["access_token"], build_tokens(other)["access_token"], order.id


@pytest.mark.asyncio
@pytest.mark.db
async def test_payment_signatures_and_refund_state(monkeypatch):
    monkeypatch.setattr(settings, "paystack_webhook_secret", "secret")
    payload = b'{"event":"charge.success"}'
    signature = hmac.new(b"secret", payload, hashlib.sha512).hexdigest()
    assert verify_webhook_signature(PaymentProvider.PAYSTACK, payload, signature) is True
    assert verify_webhook_signature(PaymentProvider.PAYSTACK, payload, "bad") is False

    monkeypatch.setattr(settings, "flutterwave_webhook_secret", "flw-secret")
    assert verify_webhook_signature(PaymentProvider.FLUTTERWAVE, b"{}", "flw-secret") is True
    assert verify_webhook_signature(PaymentProvider.FLUTTERWAVE, b"{}", "bad") is False

    monkeypatch.setattr(settings, "use_fake_external_services", False)
    await _create_paid_payment("paystack_ref")
    await _create_paid_payment("paystack_fail_ref")

    async def fake_refund(payment, amount):
        return {"refund": {"status": True, "amount": amount}}

    monkeypatch.setattr(payment_service, "_refund_paystack_payment", fake_refund)
    async with async_session() as session:
        payment = await refund_payment(session, "paystack_ref", 2500)
        assert payment.status == PaymentStatus.REFUNDED

    async with async_session() as session:
        payment = await get_payment_by_reference(session, "paystack_ref")
        assert payment.status == PaymentStatus.REFUNDED
        assert payment.provider_response["refund"]["amount"] == 2500

    async def failing_refund(payment, amount):
        raise HTTPException(status_code=502, detail="Refund failed")

    monkeypatch.setattr(payment_service, "_refund_paystack_payment", failing_refund)
    async with async_session() as session:
        with pytest.raises(HTTPException):
            await refund_payment(session, "paystack_fail_ref", 2500)

    async with async_session() as session:
        payment = await get_payment_by_reference(session, "paystack_fail_ref")
        assert payment.status == PaymentStatus.PAID


def test_payment_verify_is_owner_scoped_and_public_response_is_redacted(client):
    owner_token, other_token, _ = asyncio.run(_create_user_payment_fixture())

    other_response = client.get("/api/v1/payments/verify/owner_ref", headers={"Authorization": f"Bearer {other_token}"})
    assert other_response.status_code == 404

    owner_response = client.get("/api/v1/payments/verify/owner_ref", headers={"Authorization": f"Bearer {owner_token}"})
    assert owner_response.status_code == 200
    assert "provider_response" not in owner_response.json()


def test_payment_initiate_rejects_client_currency_tampering(client):
    owner_token, _, order_id = asyncio.run(_create_user_payment_fixture())
    response = client.post(
        "/api/v1/payments/initiate",
        json={"order_id": order_id, "provider": "paystack", "currency": "USD"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 400
