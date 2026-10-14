from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from api.deps import (
    CurrentUserDep,
    OrderServiceDep,
    ProductServiceDep,
    UserServiceDep,
    require_admin,
)
from models.order import Order, OrderStatus
from models.product import Product
from models.user import User
from schemas.order import OrderRead, OrderStatusUpdate
from schemas.product import ProductRead
from schemas.user import RoleUpdate, UserRead

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderRead,
)
async def order_change_status(
    orders: OrderServiceDep, order_id: UUID, data: OrderStatusUpdate
) -> Order:
    return await orders.change_status(order_id=order_id, new_status=data.status)


@router.patch("/users/{user_id}/role", response_model=UserRead)
async def change_user_role_by_id(
    user_id: UUID, data: RoleUpdate, users: UserServiceDep, actor: CurrentUserDep
) -> User:
    return await users.change_role(user_id=user_id, actor_id=actor.id, role=data.role)


@router.get("/orders", response_model=list[OrderRead])
async def get_all_orders(
    orders: OrderServiceDep,
    order_status: Annotated[OrderStatus | None, Query(alias="status")] = None,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    page: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Order]:
    return await orders.list_all(status=order_status, page=page, size=size)


@router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(order_id: UUID, orders: OrderServiceDep) -> Order:
    return await orders.get(order_id=order_id)


@router.get("/products", response_model=list[ProductRead])
async def get_products(
    products: ProductServiceDep,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    page: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Product]:
    return await products.list_products(page=page, size=size, include_inactive=True)


@router.get("/users", response_model=list[UserRead])
async def get_all_users(
    users: UserServiceDep,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    page: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[User]:
    return await users.list_all(page=page, size=size)


@router.post("/users/{user_id}/block", response_model=UserRead)
async def block_user(
    user_id: UUID, users: UserServiceDep, admin: CurrentUserDep
) -> User:
    return await users.block(user_id=user_id, actor_id=admin.id)


@router.post("/users/{user_id}/unblock", response_model=UserRead)
async def unblock_user(user_id: UUID, users: UserServiceDep) -> User:
    return await users.unblock(user_id=user_id)
