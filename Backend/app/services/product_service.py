from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category, Collection, Fabric, Product, ProductCollection, ProductImage
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.cloudinary_service import delete_image_if_configured, upload_image


async def get_product_by_slug(session: AsyncSession, slug: str) -> Optional[Product]:
    result = await session.execute(select(Product).where(Product.slug == slug))
    return result.scalars().unique().first()


def _product_filters(
    query,
    category_slug: str | None = None,
    collection_slug: str | None = None,
    fabric_slug: str | None = None,
    gender: str | None = None,
    featured: bool | None = None,
    bestseller: bool | None = None,
    sale: bool | None = None,
    new_arrival: bool | None = None,
    coming_soon: bool | None = None,
    preorder: bool | None = None,
    q: str | None = None,
):
    if category_slug:
        query = query.join(Product.category).where(Category.slug == category_slug)
    if fabric_slug:
        query = query.join(Product.fabric).where(Fabric.slug == fabric_slug)
    if collection_slug:
        query = query.join(Product.collections).join(ProductCollection.collection).where(Collection.slug == collection_slug)
    if gender:
        query = query.where(Product.gender == gender)
    if featured is not None:
        query = query.where(Product.is_featured == featured)
    if bestseller is not None:
        query = query.where(Product.is_bestseller == bestseller)
    if sale is not None:
        query = query.where(Product.is_sale == sale)
    if new_arrival is not None:
        query = query.where(Product.is_new_arrival == new_arrival)
    if coming_soon is not None:
        query = query.where(Product.is_coming_soon == coming_soon)
    if preorder is not None:
        query = query.where(Product.is_preorder == preorder)
    if q:
        term = f"%{q.lower()}%"
        query = query.where(or_(func.lower(Product.name).like(term), func.lower(Product.search_vector).like(term)))
    return query


async def list_products(
    session: AsyncSession,
    limit: int = 20,
    offset: int = 0,
    category_slug: str | None = None,
    collection_slug: str | None = None,
    fabric_slug: str | None = None,
    gender: str | None = None,
    featured: bool | None = None,
    bestseller: bool | None = None,
    sale: bool | None = None,
    new_arrival: bool | None = None,
    coming_soon: bool | None = None,
    preorder: bool | None = None,
    q: str | None = None,
) -> tuple[list[Product], int]:
    base = _product_filters(
        select(Product),
        category_slug,
        collection_slug,
        fabric_slug,
        gender,
        featured,
        bestseller,
        sale,
        new_arrival,
        coming_soon,
        preorder,
        q,
    )
    count_query = _product_filters(
        select(func.count(Product.id)),
        category_slug,
        collection_slug,
        fabric_slug,
        gender,
        featured,
        bestseller,
        sale,
        new_arrival,
        coming_soon,
        preorder,
        q,
    )
    total = (await session.execute(count_query)).scalar_one()
    result = await session.execute(base.order_by(Product.id.desc()).limit(limit).offset(offset))
    return result.scalars().unique().all(), total


async def list_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).order_by(Category.sort_order, Category.name))
    return result.scalars().all()


async def list_collections(session: AsyncSession) -> list[Collection]:
    result = await session.execute(select(Collection).order_by(Collection.sort_order, Collection.name))
    return result.scalars().all()


async def list_fabrics(session: AsyncSession) -> list[Fabric]:
    result = await session.execute(select(Fabric).order_by(Fabric.sort_order, Fabric.name))
    return result.scalars().all()


async def create_product(session: AsyncSession, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    product.search_vector = " ".join(filter(None, [product.name, product.description or "", product.slug]))
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def update_product(session: AsyncSession, product: Product, data: ProductUpdate) -> Product:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    product.search_vector = " ".join(filter(None, [product.name, product.description or "", product.slug]))
    await session.commit()
    await session.refresh(product)
    return product


async def add_product_image(
    session: AsyncSession,
    product: Product,
    filename: str,
    content_type: str,
    content: bytes,
    alt: str | None = None,
    sort_order: int = 0,
    is_primary: bool = False,
) -> ProductImage:
    uploaded = await upload_image(filename, content_type, content)
    if is_primary:
        for image in product.images:
            image.is_primary = False
    image = ProductImage(
        product_id=product.id,
        url=uploaded["url"],
        secure_url=uploaded.get("secure_url"),
        public_id=uploaded.get("public_id"),
        alt=alt,
        sort_order=sort_order,
        is_primary=is_primary,
        width=uploaded.get("width"),
        height=uploaded.get("height"),
        format=uploaded.get("format"),
        resource_type=uploaded.get("resource_type"),
    )
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


async def delete_product_image(session: AsyncSession, image: ProductImage) -> None:
    await delete_image_if_configured(image.public_id)
    await session.delete(image)
    await session.commit()


async def get_product_image(session: AsyncSession, image_id: int) -> ProductImage | None:
    return await session.get(ProductImage, image_id)
