import asyncio
import logging
from datetime import UTC, datetime, timedelta

from core.config import settings
from db.session import SessionLocal
from services.order import OrderService
from services.outbox import OutboxService

logger = logging.getLogger(__name__)


async def expire_once() -> None:
    async with SessionLocal() as session:
        orders = OrderService(session, outbox=OutboxService(session))
        older_than = datetime.now(UTC) - timedelta(
            hours=settings.ORDER_PICKUP_TTL_HOURS
        )
        count = await orders.expire_ready_orders(older_than=older_than)
        await session.commit()
        if count:
            logger.info("Expired %s orders", count)


async def run_expiration() -> None:
    while True:
        try:
            await expire_once()
        except Exception:
            logger.exception("Order expiration iteration failed")
        await asyncio.sleep(60)
