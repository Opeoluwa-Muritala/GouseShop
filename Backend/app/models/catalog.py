from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import Gender, ProductStatus


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    banner_url: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    products = relationship("Product", back_populates="category", lazy="selectin")


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    banner_url: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    product_links = relationship("ProductCollection", back_populates="collection", lazy="selectin")


class Fabric(Base):
    __tablename__ = "fabrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    banner_url: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    products = relationship("Product", back_populates="fabric", lazy="selectin")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    compare_at_price: Mapped[int] = mapped_column(Integer, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    fabric_id: Mapped[int] = mapped_column(ForeignKey("fabrics.id", ondelete="SET NULL"), nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, native_enum=False, values_callable=lambda enum: [item.value for item in enum]), nullable=True
    )
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=ProductStatus.ACTIVE,
        server_default=ProductStatus.ACTIVE.value,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_bestseller: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_new_arrival: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_coming_soon: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_preorder: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    search_vector: Mapped[str] = mapped_column(Text, nullable=True)

    category = relationship("Category", back_populates="products", lazy="selectin")
    fabric = relationship("Fabric", back_populates="products", lazy="selectin")
    variants = relationship("Variant", back_populates="product", lazy="selectin")
    images = relationship("ProductImage", back_populates="product", lazy="selectin")
    collections = relationship("ProductCollection", back_populates="product", lazy="selectin")


class ProductCollection(Base):
    __tablename__ = "product_collections"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)

    product = relationship("Product", back_populates="collections", lazy="selectin")
    collection = relationship("Collection", back_populates="product_links", lazy="selectin")


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    secure_url: Mapped[str] = mapped_column(String(255), nullable=True)
    public_id: Mapped[str] = mapped_column(String(255), nullable=True)
    alt: Mapped[str] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    width: Mapped[int] = mapped_column(Integer, nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    format: Mapped[str] = mapped_column(String(50), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)

    product = relationship("Product", back_populates="images", lazy="selectin")


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sku: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    size: Mapped[str] = mapped_column(String(50), nullable=True)
    color: Mapped[str] = mapped_column(String(80), nullable=True)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=True)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    reserved_qty: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    additional_price: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    product = relationship("Product", back_populates="variants", lazy="selectin")
