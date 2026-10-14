from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.deps import CurrentUserDep, OrderServiceDep, require_admin
from models import Order
from schemas.order import OrderRead, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_user_order(orders: OrderServiceDep, user: CurrentUserDep) -> Order:
    return await orders.create(user.id)


@router.get("", response_model=list[OrderRead])
async def get_all_user_orders(
    orders: OrderServiceDep, user: CurrentUserDep
) -> Sequence[Order]:
    return await orders.list_for_user(user.id)


@router.get("/{order_id}", response_model=OrderRead)
async def get_user_order(
    orders: OrderServiceDep, user: CurrentUserDep, order_id: UUID
) -> Order:
    return await orders.get(user_id=user.id, order_id=order_id)


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_user_order(
    orders: OrderServiceDep, user: CurrentUserDep, order_id: UUID
) -> Order:
    return await orders.cancel(user_id=user.id, order_id=order_id)


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_admin)],
)
async def order_change_status(
    orders: OrderServiceDep, order_id: UUID, data: OrderStatusUpdate
) -> Order:
    return await orders.change_status(order_id, data.status)
