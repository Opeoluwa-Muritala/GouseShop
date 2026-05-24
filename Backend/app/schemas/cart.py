from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variant_id: int
    quantity: int
    price_snapshot: int


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: Optional[str]
    currency: str
    items: List[CartItemRead]
