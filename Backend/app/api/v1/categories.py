from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.product import ProductList
from app.models.catalog import Category
from app.services.product_service import list_categories, list_products
from app.api.v1.deps import require_admin

router = APIRouter()


@router.get("/", response_model=list[CategoryRead])
async def read_categories(session: AsyncSession = Depends(get_session)):
    return await list_categories(session)


@router.get("/{slug}/products", response_model=ProductList)
async def category_products(slug: str, session: AsyncSession = Depends(get_session)):
    products, total = await list_products(session, category_slug=slug)
    return {"items": products, "total": total}


@router.post("/admin", response_model=CategoryRead, dependencies=[Depends(require_admin)])
async def admin_create_category(data: CategoryCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(Category).where(Category.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")
    category = Category(**data.model_dump())
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category
