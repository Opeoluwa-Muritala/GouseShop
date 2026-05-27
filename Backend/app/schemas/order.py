from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: Optional[int]
    quantity: int
    unit_price: int
    product_snapshot: Optional[dict]


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address_id: Optional[int]
    status: str
    subtotal: int
    shipping_fee: int
    discount: int
    total: int
    currency: str
    notes: Optional[str]
    tracking_number: Optional[str] = None
    items: List[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    status: str
    tracking_number: Optional[str] = None


class OrderCreate(BaseModel):
    address_id: int
    notes: Optional[str] = None
