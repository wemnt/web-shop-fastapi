from uuid import UUID

from fastapi import APIRouter, status

from api.deps import CurrentUserDep
from db.session import SessionDep
from models import CartItem
from schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from services.cart import add_item, clear_cart, get_cart, remove_item, update_item

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartRead)
async def get_user_cart(user: CurrentUserDep, session: SessionDep) -> CartRead:
    return await get_cart(session, user.id)


@router.post("/items", response_model=CartRead)
async def add_item_cart(user: CurrentUserDep, session: SessionDep, data: CartItemCreate) -> CartRead:
    await add_item(session, user.id, data)
    return await get_cart(session, user.id)


@router.patch("/items/{product_id}", response_model=CartRead)
async def update_item_cart(user: CurrentUserDep, session: SessionDep, product_id: UUID, data: CartItemUpdate) -> CartRead:
    await update_item(session, user.id, product_id, data)
    return await get_cart(session, user.id)


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_cart(user: CurrentUserDep, session: SessionDep, product_id: UUID) -> None:
    await remove_item(session, user.id, product_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_user_cart(user: CurrentUserDep, session: SessionDep) -> None:
    await clear_cart(session, user.id)
