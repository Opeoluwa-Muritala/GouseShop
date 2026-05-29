from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_admin
from app.core.database import get_session
from app.core.geo import request_country_code
from app.core.rate_limit import rate_limit
from app.models.enums import PaymentProvider, UserRole
from app.schemas.payment import PaymentAdminRead, PaymentInitiate, PaymentRead, RefundRequest
from app.services.order_service import get_order_by_id
from app.services.payment_service import (
    apply_webhook_payment_update,
    get_payment_by_reference,
    initiate_payment,
    refund_payment,
    verify_payment,
    verify_webhook_signature,
)

router = APIRouter()


@router.post("/initiate", response_model=PaymentRead, dependencies=[Depends(rate_limit("payment_initiate", 20, 60))])
async def initiate(
    data: PaymentInitiate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    order = await get_order_by_id(session, data.order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    detected_country = await request_country_code(request)
    if data.country and data.country.upper() != (detected_country or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Country must be determined by the server")
    if data.currency and data.currency.upper() != order.currency.upper():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Currency does not match the order")
    if (data.provider or "").lower() == PaymentProvider.PAYSTACK.value and order.currency.upper() not in {"NGN", "GHS", "ZAR", "KES"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Paystack does not support this order currency")
    return await initiate_payment(session, order, data.provider, detected_country, order.currency)


@router.get("/verify/{ref}", response_model=PaymentRead)
async def verify(ref: str, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    existing = await get_payment_by_reference(session, ref)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    order = await get_order_by_id(session, existing.order_id)
    if not order or (order.user_id != current_user.id and current_user.role != UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    payment = await verify_payment(session, ref)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.post("/webhook/paystack")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
):
    payload = await request.body()
    if not verify_webhook_signature(PaymentProvider.PAYSTACK, payload, x_paystack_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
    data = await request.json()
    await apply_webhook_payment_update(session, PaymentProvider.PAYSTACK, data)
    return {"detail": "Webhook accepted"}


@router.post("/webhook/flutterwave")
async def flutterwave_webhook(
    request: Request,
    verif_hash: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
):
    payload = await request.body()
    if not verify_webhook_signature(PaymentProvider.FLUTTERWAVE, payload, verif_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
    data = await request.json()
    await apply_webhook_payment_update(session, PaymentProvider.FLUTTERWAVE, data)
    return {"detail": "Webhook accepted"}


@router.post("/refund", response_model=PaymentAdminRead, dependencies=[Depends(require_admin)])
async def refund(data: RefundRequest, session: AsyncSession = Depends(get_session)):
    payment = await refund_payment(session, data.reference, data.amount)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
