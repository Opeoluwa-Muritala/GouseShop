from typing import Optional

from pydantic import BaseModel, ConfigDict


class PaymentInitiate(BaseModel):
    order_id: int
    provider: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    provider: str
    provider_reference: str
    provider_checkout_url: Optional[str]
    amount: int
    currency: str
    status: str


class PaymentAdminRead(PaymentRead):
    provider_response: Optional[dict] = None


class RefundRequest(BaseModel):
    reference: str
    amount: Optional[int] = None
