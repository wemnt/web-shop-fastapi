from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions import (
    EmptyCartError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    OrderNotFoundError,
)
from models import CartItem, Order, OrderItem, Product
from models.order import OrderStatus
from services.cart import CartService

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {
        OrderStatus.DELIVERING,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.CANCELLED,
    },
    OrderStatus.DELIVERING: {
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.READY_FOR_PICKUP: {
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}

USER_CANCELLABLE = {OrderStatus.CREATED, OrderStatus.READY_FOR_PICKUP}


class OrderService:
    def __init__(self, session: AsyncSession, cart: CartService) -> None:
        self.session = session
        self.cart = cart

    async def create(self, user_id: UUID) -> Order:
        cart_items = (
            await self.session.scalars(
                select(CartItem)
                .where(CartItem.user_id == user_id)
                .order_by(CartItem.product_id)
            )
        ).all()
        if not cart_items:
            raise EmptyCartError("Cart is empty")
        ids = [item.product_id for item in cart_items]
        products = (
            await self.session.scalars(
                select(Product)
                .where(Product.id.in_(ids))
                .order_by(Product.id)
                .with_for_update()
            )
        ).all()
        products_by_id = {p.id: p for p in products}

        order_items: list[OrderItem] = []
        total = Decimal("0.00")
        for cart_item in cart_items:
            product = products_by_id.get(cart_item.product_id)
            if product is None:
                raise InsufficientStockError("Product is unavailable")
            if (
                product.stock < cart_item.quantity
                or product.deleted_at is not None
                or not product.is_active
            ):
                raise InsufficientStockError(f"Product '{product.name}' is unavailable")
            product.stock -= cart_item.quantity
            order_items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    name=product.name,
                    price=product.price,
                )
            )
            total += product.price * cart_item.quantity

        order = Order(user_id=user_id, total=total, items=order_items)
        self.session.add(order)
        await self.cart.clear(user_id)
        await self.session.flush()
        return order

    async def list_for_user(self, user_id: UUID) -> Sequence[Order]:
        return (
            await self.session.scalars(
                select(Order)
                .where(Order.user_id == user_id)
                .options(selectinload(Order.items))
                .order_by(Order.created_at.desc())
            )
        ).all()

    async def get(self, *, user_id: UUID | None = None, order_id: UUID) -> Order:
        query = (
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        if user_id is not None:
            query = query.where(Order.user_id == user_id)

        order = await self.session.scalar(query)
        if order is None:
            raise OrderNotFoundError("Order not found")

        return order

    async def _restock(self, order: Order) -> None:
        ids = [item.product_id for item in order.items]
        products = (
            await self.session.scalars(
                select(Product)
                .where(Product.id.in_(ids))
                .order_by(Product.id)
                .with_for_update()
            )
        ).all()
        products_by_id = {p.id: p for p in products}

        for item in order.items:
            products_by_id[item.product_id].stock += item.quantity

    async def _apply_status(self, order: Order, new_status: OrderStatus) -> None:
        if new_status not in ALLOWED_TRANSITIONS[order.status]:
            raise InvalidStatusTransitionError(
                f"Cannot change status from '{order.status}' to '{new_status}'"
            )
        if new_status == OrderStatus.CANCELLED:
            await self._restock(order)
        if new_status == OrderStatus.READY_FOR_PICKUP:
            order.ready_at = datetime.now(tz=UTC)
        order.status = new_status

    async def _get_order_for_update(
        self, *, order_id: UUID, user_id: UUID | None = None
    ) -> Order:
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
            .with_for_update()
        )
        if user_id is not None:
            query = query.where(Order.user_id == user_id)
        order = await self.session.scalar(query)
        if order is None:
            raise OrderNotFoundError("Order not found")
        return order

    async def change_status(self, *, order_id: UUID, new_status: OrderStatus) -> Order:
        order = await self._get_order_for_update(order_id=order_id)
        await self._apply_status(order, new_status)
        return order

    async def cancel(self, *, user_id: UUID, order_id: UUID) -> Order:
        order = await self._get_order_for_update(order_id=order_id, user_id=user_id)
        if order.status not in USER_CANCELLABLE:
            raise InvalidStatusTransitionError(
                f"Order can't be cancelled in status {order.status}"
            )
        await self._apply_status(order, OrderStatus.CANCELLED)
        return order

    async def list_all(
        self, *, status: OrderStatus | None = None, page: int, size: int
    ) -> Sequence[Order]:
        query = (
            select(Order)
            .order_by(Order.created_at.desc())
            .options(selectinload(Order.items))
        )
        if status is not None:
            query = query.where(Order.status == status)
        query = query.limit(size).offset(page * size)
        result = await self.session.scalars(query)
        return result.all()
