from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.product import ProductCreate, ProductList, ProductRead, ProductUpdate
from app.services.product_service import create_product, get_product_by_slug, list_products, update_product
from app.api.v1.deps import require_admin

router = APIRouter()


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
