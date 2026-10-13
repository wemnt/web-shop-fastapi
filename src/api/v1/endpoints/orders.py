from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.deps import CurrentUserDep, require_admin
from db.session import SessionDep
from models import Order
from schemas.order import OrderRead, OrderStatusUpdate
from services.order import (
    cancel_order,
    change_order_status,
    create_order,
    get_order,
    get_user_orders,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_user_order(session: SessionDep, user: CurrentUserDep) -> Order:
    return await create_order(session, user.id)


@router.get("", response_model=list[OrderRead])
async def get_all_user_orders(
    session: SessionDep, user: CurrentUserDep
) -> Sequence[Order]:
    return await get_user_orders(session, user.id)


@router.get("/{order_id}", response_model=OrderRead)
async def get_user_order(
    session: SessionDep, user: CurrentUserDep, order_id: UUID
) -> Order:
    return await get_order(session, user.id, order_id)


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_user_order(
    session: SessionDep, user: CurrentUserDep, order_id: UUID
) -> Order:
    return await cancel_order(session, user.id, order_id)


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_admin)],
)
async def order_change_status(
    session: SessionDep, order_id: UUID, data: OrderStatusUpdate
) -> Order:
    return await change_order_status(session, order_id, data.status)
