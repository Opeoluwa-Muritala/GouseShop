from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class WishlistCreate(BaseModel):
    product_id: int


class WishlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    rating: int
    title: Optional[str]
    body: Optional[str]
    is_approved: bool


class WaitlistCreate(BaseModel):
    email: EmailStr
    product_id: Optional[int] = None
    variant_id: Optional[int] = None


class NewsletterCreate(BaseModel):
    email: EmailStr
