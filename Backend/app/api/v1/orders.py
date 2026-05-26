from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.order import OrderRead, OrderStatusUpdate
from app.services.cart_service import get_cart
from app.services.order_service import cancel_order, create_order_from_cart, get_order_by_id, list_user_orders, update_order_status
from app.api.v1.deps import get_current_user, require_admin

router = APIRouter()


@router.post("/", response_model=OrderRead)
async def create_order(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    cart = await get_cart(session, user_id=current_user.id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active cart")
    try:
        return await create_order_from_cart(session, cart_id=cart.id, currency="USD")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[OrderRead])
async def get_orders(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return await list_user_orders(session, current_user.id)


@router.get("/admin/list", response_model=list[OrderRead], dependencies=[Depends(require_admin)])
async def admin_list_orders(session: AsyncSession = Depends(get_session)):
    from sqlalchemy import select
    from app.models.order import Order

    result = await session.execute(select(Order).order_by(Order.created_at.desc()))
    return result.scalars().unique().all()


@router.patch("/admin/{order_id}/status", response_model=OrderRead, dependencies=[Depends(require_admin)])
async def admin_update_order_status(
    order_id: int, data: OrderStatusUpdate, session: AsyncSession = Depends(get_session)
):
    order = await get_order_by_id(session, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    try:
        return await update_order_status(session, order, data.status, data.tracking_number)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status")


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    order = await get_order_by_id(session, order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.get("/{order_id}/tracking")
async def get_order_tracking(order_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    order = await get_order_by_id(session, order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return {"order_id": order.id, "status": order.status, "tracking_number": order.tracking_number}


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_user_order(order_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    order = await get_order_by_id(session, order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    try:
        return await cancel_order(session, order)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
