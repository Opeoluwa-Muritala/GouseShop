from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem
from app.models.catalog import Variant


async def get_cart(session: AsyncSession, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Optional[Cart]:
    query = select(Cart)
    if user_id is not None:
        query = query.where(Cart.user_id == user_id)
    elif session_id is not None:
        query = query.where(Cart.session_id == session_id)
    else:
        return None

    result = await session.execute(query)
    return result.scalars().unique().first()


async def create_cart(session: AsyncSession, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Cart:
    cart = Cart(user_id=user_id, session_id=session_id)
    session.add(cart)
    await session.commit()
    await session.refresh(cart)
    return cart


async def get_or_create_cart(session: AsyncSession, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Cart:
    cart = await get_cart(session, user_id=user_id, session_id=session_id)
    if cart:
        return cart
    return await create_cart(session, user_id=user_id, session_id=session_id)


async def add_item_to_cart(session: AsyncSession, cart: Cart, variant_id: int, quantity: int) -> CartItem:
    variant = await session.get(Variant, variant_id)
    if not variant:
        raise ValueError("Variant not found")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")
    if variant.stock_qty - variant.reserved_qty < quantity:
        raise ValueError("Insufficient inventory")

    result = await session.execute(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id))
    item = result.scalar_one_or_none()

    if item:
        if variant.stock_qty - variant.reserved_qty < item.quantity + quantity:
            raise ValueError("Insufficient inventory")
        item.quantity += quantity
    else:
        base_price = variant.product.price if variant.product else 0
        item = CartItem(
            cart_id=cart.id,
            variant_id=variant_id,
            quantity=quantity,
            price_snapshot=base_price + (variant.additional_price or 0),
        )
        cart.items.append(item)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        result = await session.execute(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id))
        item = result.scalar_one()
        item.quantity += quantity
        await session.commit()
    await session.refresh(item)
    await session.refresh(cart)
    return item


async def update_cart_item(session: AsyncSession, cart: Cart, item_id: int, quantity: int) -> Cart:
    item = next((existing for existing in cart.items if existing.id == item_id), None)
    if item is None:
        raise ValueError("Cart item not found")
    if quantity == 0:
        await session.delete(item)
    else:
        variant = await session.get(Variant, item.variant_id)
        if variant is None:
            raise ValueError("Variant not found")
        if variant.stock_qty - variant.reserved_qty < quantity:
            raise ValueError("Insufficient inventory")
        item.quantity = quantity
    await session.commit()
    await session.refresh(cart)
    return cart


async def clear_cart(session: AsyncSession, cart: Cart) -> None:
    for item in list(cart.items):
        await session.delete(item)
    await session.commit()


async def merge_guest_cart_into_user_cart(session: AsyncSession, session_id: str, user_id: int) -> Cart | None:
    guest_cart = await get_cart(session, session_id=session_id)
    if guest_cart is None:
        return None
    user_cart = await get_or_create_cart(session, user_id=user_id)
    for guest_item in list(guest_cart.items):
        existing = next((item for item in user_cart.items if item.variant_id == guest_item.variant_id), None)
        if existing:
            existing.quantity += guest_item.quantity
            await session.delete(guest_item)
        else:
            guest_item.cart_id = user_cart.id
    await session.delete(guest_cart)
    await session.commit()
    await session.refresh(user_cart)
    return user_cart
