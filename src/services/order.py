from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import CartItem, Order, OrderItem, Product
from schemas.order import OrderItemRead, OrderRead, OrderStatusUpdate
from services.cart import delete_cart_items, get_cart
from services.exceptions import (
    EmptyCartError,
    InsufficientStockError,
    OrderNotFoundError,
)


async def create_order(session: AsyncSession, user_id: UUID) -> Order:
    cart_items = (
        await session.scalars(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.product_id)
        )
    ).all()
    if not cart_items:
        raise EmptyCartError("Cart is empty")
    ids = [item.product_id for item in cart_items]
    products = (
        await session.scalars(
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
    session.add(order)
    await delete_cart_items(session, user_id)
    await session.commit()
    return order


async def get_user_orders(session: AsyncSession, user_id: UUID) -> Sequence[Order]:
    return (
        await session.scalars(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
        )
    ).all()


async def get_order(session: AsyncSession, user_id: UUID, order_id: UUID) -> Order:
    order = await session.scalar(
        select(Order)
        .where(Order.user_id == user_id, Order.id == order_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )

    if order is None:
        raise OrderNotFoundError("Order not found")

    return order
