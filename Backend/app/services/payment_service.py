from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrderStatus, PaymentProvider, PaymentStatus
from app.models.order import Order
from app.models.payment import Payment


SUPPORTED_PAYSTACK_COUNTRIES = {"NG", "GH", "ZA", "KE"}


def choose_provider(provider: str | None = None, country: str | None = None) -> PaymentProvider:
    if provider:
        return PaymentProvider(provider)
    if country and country.upper() in SUPPORTED_PAYSTACK_COUNTRIES:
        return PaymentProvider.PAYSTACK
    return PaymentProvider.FLUTTERWAVE


async def initiate_payment(
    session: AsyncSession, order: Order, provider: str | None = None, country: str | None = None, currency: str = "USD"
) -> Payment:
    selected = choose_provider(provider, country)
    reference = f"{selected.value}_{uuid4().hex}"
    payment = Payment(
        order_id=order.id,
        provider=selected,
        provider_reference=reference,
        provider_checkout_url=f"https://checkout.gouseshop.local/{reference}",
        amount=order.total,
        currency=currency or order.currency,
        status=PaymentStatus.INITIALIZED,
        provider_response={"mode": "fake", "reference": reference},
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
    payment.status = PaymentStatus.PAID
    payment.verified_at = datetime.utcnow()
    payment.provider_response = {**(payment.provider_response or {}), "verified": True}
    order = await session.get(Order, payment.order_id)
    if order:
        order.status = OrderStatus.PAID
        order.paid_at = datetime.utcnow()
    await session.commit()
    await session.refresh(payment)
    return payment


async def refund_payment(session: AsyncSession, reference: str, amount: int | None = None) -> Payment | None:
    payment = await get_payment_by_reference(session, reference)
    if payment is None:
        return None
    payment.status = PaymentStatus.REFUNDED
    payment.provider_response = {**(payment.provider_response or {}), "refund_amount": amount or payment.amount}
    order = await session.get(Order, payment.order_id)
    if order:
        order.status = OrderStatus.REFUNDED
    await session.commit()
    await session.refresh(payment)
    return payment


def verify_webhook_signature(provider: PaymentProvider, payload: bytes, signature: str | None) -> bool:
    return bool(signature) or provider == PaymentProvider.FAKE
