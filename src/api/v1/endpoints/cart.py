from uuid import UUID

from fastapi import APIRouter, status

from api.deps import CartServiceDep, CurrentUserDep
from schemas.cart import CartItemCreate, CartItemUpdate, CartRead

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartRead)
async def get_user_cart(user: CurrentUserDep, cart: CartServiceDep) -> CartRead:
    return await cart.get(user.id)


@router.post("/items", response_model=CartRead)
async def add_item_cart(
    user: CurrentUserDep, cart: CartServiceDep, data: CartItemCreate
) -> CartRead:
    await cart.add(user.id, data)
    return await cart.get(user.id)


@router.patch("/items/{product_id}", response_model=CartRead)
async def update_item_cart(
    user: CurrentUserDep, cart: CartServiceDep, product_id: UUID, data: CartItemUpdate
) -> CartRead:
    await cart.update(user_id=user.id, product_id=product_id, data=data)
    return await cart.get(user.id)


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_cart(
    user: CurrentUserDep, cart: CartServiceDep, product_id: UUID
) -> None:
    await cart.remove(user_id=user.id, product_id=product_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_user_cart(user: CurrentUserDep, cart: CartServiceDep) -> None:
    await cart.clear(user.id)
