from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_admin
from app.core.database import get_session
from app.core.geo import request_country_code, request_paystack_currency, request_currency
from app.core.rate_limit import rate_limit
from app.models.enums import PaymentProvider
from app.schemas.payment import PaymentInitiate, PaymentRead, RefundRequest
from app.services.order_service import get_order_by_id
from app.services.payment_service import initiate_payment, refund_payment, verify_payment, verify_webhook_signature

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
    detected_country = data.country or await request_country_code(request)
    detected_currency = data.currency
    if not detected_currency:
        if (data.provider or "").lower() == PaymentProvider.PAYSTACK.value:
            detected_currency = await request_paystack_currency(request)
        else:
            detected_currency = await request_currency(request)
    if (data.provider or "").lower() == PaymentProvider.PAYSTACK.value and order.currency != detected_currency:
        order.currency = detected_currency
    return await initiate_payment(session, order, data.provider, detected_country, detected_currency)


@router.get("/verify/{ref}", response_model=PaymentRead)
async def verify(ref: str, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
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
    return {"detail": "Webhook accepted"}


@router.post("/refund", response_model=PaymentRead, dependencies=[Depends(require_admin)])
async def refund(data: RefundRequest, session: AsyncSession = Depends(get_session)):
    payment = await refund_payment(session, data.reference, data.amount)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
