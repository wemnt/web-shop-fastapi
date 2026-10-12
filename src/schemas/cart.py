from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

MAX_CART_ITEM_QUANTITY = 99


class CartItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=MAX_CART_ITEM_QUANTITY)


class CartItemRead(BaseModel):
    product_id: UUID
    quantity: int
    price: Decimal
    name: str
    is_available: bool
    subtotal: Decimal


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=MAX_CART_ITEM_QUANTITY)


class CartRead(BaseModel):
    items: list[CartItemRead]
    total: Decimal
