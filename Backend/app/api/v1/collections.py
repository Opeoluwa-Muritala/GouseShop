from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.product import ProductList
from app.models.catalog import Collection
from app.services.product_service import list_collections, list_products
from app.api.v1.deps import require_admin

router = APIRouter()


@router.get("/", response_model=list[CategoryRead])
async def read_collections(session: AsyncSession = Depends(get_session)):
    return await list_collections(session)


@router.get("/{slug}/products", response_model=ProductList)
async def collection_products(slug: str, session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, collection_slug=slug)
    return {"items": products, "total": total}


@router.post("/admin", response_model=CategoryRead, dependencies=[Depends(require_admin)])
async def admin_create_collection(data: CategoryCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(Collection).where(Collection.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")
    collection = Collection(**data.model_dump())
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return collection
