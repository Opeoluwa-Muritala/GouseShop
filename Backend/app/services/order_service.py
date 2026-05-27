from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.catalog import Variant
from app.models.enums import OrderStatus
from app.models.user import Address


async def create_order_from_cart(
    session: AsyncSession,
    cart_id: int,
    user_id: int,
    address_id: int,
    notes: str | None = None,
    currency: str = "NGN",
) -> Order:
    cart = await session.get(Cart, cart_id)
    if cart is None:
        raise ValueError("Cart not found")
    if cart.user_id != user_id:
        raise ValueError("Cart not found")

    items = cart.items
    if not items:
        raise ValueError("Cart is empty")

    address = await session.get(Address, address_id)
    if address is None or address.user_id != user_id:
        raise ValueError("Shipping address not found")

    subtotal = 0
    order = Order(user_id=cart.user_id, address_id=address_id, notes=notes, currency=currency)
    session.add(order)
    await session.flush()

    for item in items:
        reservation = await session.execute(
            update(Variant)
            .where(Variant.id == item.variant_id)
            .where((Variant.stock_qty - Variant.reserved_qty) >= item.quantity)
            .values(reserved_qty=Variant.reserved_qty + item.quantity)
        )
        if reservation.rowcount != 1:
            raise ValueError("Insufficient inventory")

        variant = await session.get(Variant, item.variant_id)
        if variant is None:
            raise ValueError("Variant missing")

        price = (variant.product.price if variant.product else 0) + (variant.additional_price or 0)
        line_price = price * item.quantity
        subtotal += line_price
        order_item = OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            quantity=item.quantity,
            unit_price=price,
            product_snapshot={
                "product_name": variant.product.name if variant.product else "Unknown",
                "sku": variant.sku,
                "size": variant.size,
                "color": variant.color,
            },
        )
        session.add(order_item)

    order.subtotal = subtotal
    order.total = subtotal
    for item in list(cart.items):
        await session.delete(item)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order_by_id(session: AsyncSession, order_id: int, user_id: int | None = None):
    query = select(Order).where(Order.id == order_id)
    if user_id is not None:
        query = query.where(Order.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().unique().first()


async def list_user_orders(session: AsyncSession, user_id: int):
    result = await session.execute(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()))
    return result.scalars().all()


async def cancel_order(session: AsyncSession, order: Order) -> Order:
    if order.status not in {OrderStatus.PENDING_PAYMENT, OrderStatus.PAID}:
        raise ValueError("Order cannot be cancelled")
    for item in order.items:
        if item.variant_id:
            variant = await session.get(Variant, item.variant_id)
            if variant:
                variant.reserved_qty = max(0, variant.reserved_qty - item.quantity)
    order.status = OrderStatus.CANCELLED
    await session.commit()
    await session.refresh(order)
    return order


async def update_order_status(
    session: AsyncSession, order: Order, status: str, tracking_number: str | None = None
) -> Order:
    order.status = OrderStatus(status)
    if tracking_number is not None:
        order.tracking_number = tracking_number
    await session.commit()
    await session.refresh(order)
    return order
