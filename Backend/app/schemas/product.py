from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    size: Optional[str]
    color: Optional[str]
    color_hex: Optional[str]
    stock_qty: int
    reserved_qty: int
    additional_price: int


class ProductImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    secure_url: Optional[str] = None
    public_id: Optional[str] = None
    alt: Optional[str]
    sort_order: int
    is_primary: bool


class ProductBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: int
    compare_at_price: Optional[int] = None
    category_id: Optional[int] = None
    fabric_id: Optional[int] = None
    gender: Optional[str] = None
    status: Optional[str] = "active"
    is_featured: Optional[bool] = False
    is_bestseller: Optional[bool] = False
    is_sale: Optional[bool] = False
    is_new_arrival: Optional[bool] = False
    is_coming_soon: Optional[bool] = False
    is_preorder: Optional[bool] = False


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    variants: List[VariantRead] = []
    images: List[ProductImageRead] = []


class ProductList(BaseModel):
    items: List[ProductRead]
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class ProductCreate(ProductBase):
    name: str
    slug: str
    price: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    compare_at_price: Optional[int] = None
    category_id: Optional[int] = None
    fabric_id: Optional[int] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    is_sale: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    is_coming_soon: Optional[bool] = None
    is_preorder: Optional[bool] = None
