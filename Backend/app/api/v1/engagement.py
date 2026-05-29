from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.core.rate_limit import rate_limit
from app.models.engagement import NewsletterSubscriber, Review, WaitlistEntry, WishlistItem
from app.schemas.engagement import NewsletterCreate, ReviewCreate, ReviewRead, WaitlistCreate, WishlistCreate, WishlistRead

router = APIRouter()


@router.get("/wishlist", response_model=list[WishlistRead])
async def list_wishlist(session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    result = await session.execute(select(WishlistItem).where(WishlistItem.user_id == current_user.id))
    return result.scalars().all()


@router.post("/wishlist", response_model=WishlistRead)
async def add_wishlist(data: WishlistCreate, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    item = WishlistItem(user_id=current_user.id, product_id=data.product_id)
    session.add(item)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already in wishlist")
    await session.refresh(item)
    return item


@router.delete("/wishlist/{product_id}")
async def remove_wishlist(product_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    result = await session.execute(
        select(WishlistItem).where(WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
    await session.delete(item)
    await session.commit()
    return {"detail": "Removed"}


@router.get("/reviews/{product_id}", response_model=list[ReviewRead])
async def list_reviews(product_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Review).where(Review.product_id == product_id, Review.is_approved == True))
    return result.scalars().all()


@router.post("/reviews", response_model=ReviewRead, dependencies=[Depends(rate_limit("reviews_submit", 10, 60))])
async def submit_review(data: ReviewCreate, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    review = Review(user_id=current_user.id, **data.model_dump())
    session.add(review)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review already submitted")
    await session.refresh(review)
    return review


@router.post("/waitlist", dependencies=[Depends(rate_limit("waitlist_join", 10, 60))])
async def join_waitlist(data: WaitlistCreate, session: AsyncSession = Depends(get_session)):
    entry = WaitlistEntry(**data.model_dump())
    session.add(entry)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
    return {"detail": "Waitlist signup recorded"}


@router.post("/newsletter", dependencies=[Depends(rate_limit("newsletter_subscribe", 10, 60))])
async def subscribe_newsletter(data: NewsletterCreate, session: AsyncSession = Depends(get_session)):
    subscriber = NewsletterSubscriber(email=data.email)
    session.add(subscriber)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
    return {"detail": "Newsletter signup recorded"}
