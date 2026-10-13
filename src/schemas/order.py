from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from models.order import OrderStatus


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    name: str
    price: Decimal
    quantity: int

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: OrderStatus
    total: Decimal
    created_at: datetime
    items: list[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
