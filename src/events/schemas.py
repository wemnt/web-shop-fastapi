from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar
from uuid import UUID, uuid7

from pydantic import BaseModel, Field


class CancelledBy(StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SYSTEM = "system"


class Event(BaseModel):
    subject: ClassVar[str]
    event_id: UUID = Field(default_factory=uuid7)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderCreated(Event):
    subject: ClassVar[str] = "orders.created"
    order_id: UUID
    user_id: UUID
    total: Decimal


class OrderCancelled(Event):
    subject: ClassVar[str] = "orders.cancelled"
    order_id: UUID
    user_id: UUID
    cancelled_by: CancelledBy
    actor_id: UUID | None = None
