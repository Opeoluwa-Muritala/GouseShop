from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.rate_limit import rate_limit
from app.schemas.product import ProductCreate, ProductImageRead, ProductList, ProductRead, ProductUpdate
from app.services.product_service import (
    add_product_image,
    create_product,
    delete_product_image,
    get_product_by_slug,
    get_product_image,
    list_products,
    update_product,
)
from app.api.v1.deps import require_admin

router = APIRouter()


IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    "image/webp": (b"RIFF",),
}


async def _read_limited_image(file: UploadFile) -> bytes:
    limit = settings.cloudinary_max_upload_bytes
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large")
    content_type = file.content_type or ""
    signatures = IMAGE_SIGNATURES.get(content_type)
    if not signatures or not any(content.startswith(signature) for signature in signatures):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported or invalid image content")
    if content_type == "image/webp" and content[8:12] != b"WEBP":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported or invalid image content")
    return content


@router.get("/", response_model=ProductList)
async def read_products(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = None,
    collection: str | None = None,
    fabric: str | None = None,
    gender: str | None = None,
    featured: bool | None = None,
    bestseller: bool | None = None,
    sale: bool | None = None,
    new_arrival: bool | None = None,
    coming_soon: bool | None = None,
    preorder: bool | None = None,
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    products, total = await list_products(
        session,
        limit=limit,
        offset=offset,
        category_slug=category,
        collection_slug=collection,
        fabric_slug=fabric,
        gender=gender,
        featured=featured,
        bestseller=bestseller,
        sale=sale,
        new_arrival=new_arrival,
        coming_soon=coming_soon,
        preorder=preorder,
        q=q,
    )
    return {"items": products, "total": total, "limit": limit, "offset": offset}


@router.get("/featured", response_model=ProductList)
async def featured_products(session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, featured=True)
    return {"items": products, "total": total}


@router.get("/new-arrivals", response_model=ProductList)
async def new_arrivals(session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, new_arrival=True)
    return {"items": products, "total": total}


@router.get("/bestsellers", response_model=ProductList)
async def bestsellers(session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, bestseller=True)
    return {"items": products, "total": total}


@router.get("/sale", response_model=ProductList)
async def sale_products(session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, sale=True)
    return {"items": products, "total": total}


@router.get("/coming-soon", response_model=ProductList)
async def coming_soon_products(session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, coming_soon=True)
    return {"items": products, "total": total}


@router.get("/pre-order", response_model=ProductList)
async def preorder_products(session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, preorder=True)
    return {"items": products, "total": total}


@router.get("/{slug}", response_model=ProductRead)
async def read_product(slug: str, session: AsyncSession = Depends(get_session)):
    product = await get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/admin", response_model=ProductRead, dependencies=[Depends(require_admin)])
async def admin_create_product(data: ProductCreate, session: AsyncSession = Depends(get_session)):
    return await create_product(session, data)


@router.patch("/admin/{slug}", response_model=ProductRead, dependencies=[Depends(require_admin)])
async def admin_update_product(slug: str, data: ProductUpdate, session: AsyncSession = Depends(get_session)):
    product = await get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return await update_product(session, product, data)


@router.delete("/admin/{slug}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def admin_delete_product(slug: str, session: AsyncSession = Depends(get_session)):
    product = await get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await session.delete(product)
    await session.commit()


@router.post(
    "/admin/{slug}/images",
    response_model=ProductImageRead,
    dependencies=[Depends(require_admin), Depends(rate_limit("admin_image_upload", 20, 60))],
)
async def admin_upload_product_image(
    slug: str,
    file: UploadFile = File(...),
    alt: str | None = Form(None),
    sort_order: int = Form(0),
    is_primary: bool = Form(False),
    session: AsyncSession = Depends(get_session),
):
    product = await get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    content = await _read_limited_image(file)
    return await add_product_image(
        session,
        product,
        filename=file.filename or "product-image",
        content_type=file.content_type or "",
        content=content,
        alt=alt,
        sort_order=sort_order,
        is_primary=is_primary,
    )


@router.delete("/admin/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def admin_delete_product_image(image_id: int, session: AsyncSession = Depends(get_session)):
    image = await get_product_image(session, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    await delete_product_image(session, image)
