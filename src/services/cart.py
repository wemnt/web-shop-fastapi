from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import CartItem, Product
from schemas.cart import (
    MAX_CART_ITEM_QUANTITY,
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
)
from services.exceptions import CartItemNotFoundError, CartQuantityLimitError
from services.product import get_product


async def add_item(session: AsyncSession, user_id: UUID, data: CartItemCreate) -> None:

    _ = await get_product(session, data.product_id, include_inactive=False)

    insert_stmt = insert(CartItem).values(
        user_id=user_id, product_id=data.product_id, quantity=data.quantity
    )
    stmt = insert_stmt.on_conflict_do_update(
        index_elements=[CartItem.user_id, CartItem.product_id],
        set_={
            "quantity": CartItem.quantity + insert_stmt.excluded.quantity,
            "updated_at": func.now(),
        },
    ).returning(CartItem.quantity)

    quantity = (await session.execute(stmt)).scalar_one()

    if quantity > MAX_CART_ITEM_QUANTITY:
        await session.rollback()
        raise CartQuantityLimitError("Too many items in cart")

    await session.commit()


async def get_cart(session: AsyncSession, user_id: UUID) -> CartRead:

    query = (
        select(CartItem, Product)
        .join(Product)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.created_at)
    )
    result = await session.execute(query)

    items: list[CartItemRead] = []
    total = Decimal("0.00")

    for cart_item, product in result:
        is_available = (
            product.is_active
            and product.deleted_at is None
            and product.stock >= cart_item.quantity
        )

        subtotal = product.price * cart_item.quantity

        items.append(
            CartItemRead(
                product_id=product.id,
                quantity=cart_item.quantity,
                is_available=is_available,
                subtotal=subtotal,
                name=product.name,
                price=product.price,
            )
        )

        if is_available:
            total += subtotal

    return CartRead(items=items, total=total)


async def update_item(
    session: AsyncSession, user_id: UUID, product_id: UUID, data: CartItemUpdate
) -> None:
    cart_item = await session.get(CartItem, (user_id, product_id))
    if cart_item is None:
        raise CartItemNotFoundError("Product not found in cart")
    cart_item.quantity = data.quantity
    await session.commit()


async def remove_item(session: AsyncSession, user_id: UUID, product_id: UUID) -> None:
    _ = await session.execute(
        delete(CartItem).where(
            CartItem.user_id == user_id, CartItem.product_id == product_id
        )
    )
    await session.commit()


async def clear_cart(session: AsyncSession, user_id: UUID) -> None:
    _ = await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()
