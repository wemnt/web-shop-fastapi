import logging

from db.session import SessionLocal
from events.broker import broker, orders_stream
from events.schemas import OrderCancelled, OrderCreated
from worker.idempotency import mark_processed

logger = logging.getLogger(__name__)

CONSUMER = "notifications"


@broker.subscriber(
    "orders.created",
    stream=orders_stream,
    durable="notifications-orders-created",
)
async def on_order_created(event: OrderCreated) -> None:
    async with SessionLocal() as session:
        if not await mark_processed(
            session, event_id=event.event_id, consumer=CONSUMER
        ):
            logger.info("Duplicate event %s skipped", event.event_id)
            return
        logger.info("Notify user %s: order %s created", event.user_id, event.order_id)
        await session.commit()


@broker.subscriber(
    "orders.cancelled",
    stream=orders_stream,
    durable="notifications-orders-cancelled",
)
async def on_order_cancelled(event: OrderCancelled) -> None:
    async with SessionLocal() as session:
        if not await mark_processed(
            session, event_id=event.event_id, consumer=CONSUMER
        ):
            logger.info("Duplicate event %s skipped", event.event_id)
            return
        logger.info(
            "Notify user %s: order %s cancelled by %s",
            event.user_id,
            event.order_id,
            event.cancelled_by,
        )
        await session.commit()
