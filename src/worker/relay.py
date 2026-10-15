import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from db.session import SessionLocal
from events.broker import broker
from models import OutboxEvent

logger = logging.getLogger(__name__)

relay_task: asyncio.Task[None] | None = None


async def publish_pending() -> None:
    async with SessionLocal() as session:
        rows = await session.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at.asc())
            .limit(100)
            .with_for_update(skip_locked=True)
        )

        for row in rows:
            await broker.publish(
                row.payload,
                subject=row.subject,
                stream="ORDERS",
                headers={"Nats-Msg-Id": str(row.id)},
            )
            row.published_at = datetime.now(tz=UTC)

        await session.commit()


async def run_relay() -> None:
    while True:
        try:
            await publish_pending()
        except Exception:
            logger.exception("Outbox relay iteration failed")
        await asyncio.sleep(1)
