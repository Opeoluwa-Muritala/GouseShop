from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.services.cart_service import add_item_to_cart, clear_cart, get_or_create_cart, get_cart, update_cart_item
from app.api.v1.deps import get_optional_current_user

router = APIRouter()


@router.get("/", response_model=CartRead)
async def fetch_cart(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_current_user),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    user_id = current_user.id if current_user else None
    if user_id is None and not x_session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Session-Id is required for guest carts")
    cart = await get_cart(session, user_id=user_id, session_id=x_session_id)
    if cart is None:
        cart = await get_or_create_cart(session, user_id=user_id, session_id=x_session_id if user_id is None else None)
    return cart


@router.post("/items", response_model=CartRead)
async def add_item(
    item: CartItemCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_current_user),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    user_id = current_user.id if current_user else None
    if user_id is None and not x_session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Session-Id is required for guest carts")
    cart = await get_or_create_cart(session, user_id=user_id, session_id=x_session_id if user_id is None else None)
    try:
        await add_item_to_cart(session, cart, item.variant_id, item.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await session.refresh(cart)
    return cart


@router.patch("/items/{item_id}", response_model=CartRead)
async def update_item(
    item_id: int,
    item: CartItemUpdate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_current_user),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    user_id = current_user.id if current_user else None
    cart = await get_cart(session, user_id=user_id, session_id=x_session_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    try:
        return await update_cart_item(session, cart, item_id, item.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/items/{item_id}")
async def remove_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_current_user),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    user_id = current_user.id if current_user else None
    cart = await get_cart(session, user_id=user_id, session_id=x_session_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    item = next((i for i in cart.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    await session.delete(item)
    await session.commit()
    return {"detail": "Item removed"}


@router.delete("/")
async def clear_user_cart(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_current_user),
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
):
    user_id = current_user.id if current_user else None
    cart = await get_cart(session, user_id=user_id, session_id=x_session_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    await clear_cart(session, cart)
    return {"detail": "Cart cleared"}
