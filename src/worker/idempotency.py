from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.processed_event import ProcessedEvent


async def mark_processed(
    session: AsyncSession, *, event_id: UUID, consumer: str
) -> bool:
    stmt = (
        insert(ProcessedEvent)
        .values(event_id=event_id, consumer=consumer)
        .on_conflict_do_nothing()
        .returning(ProcessedEvent.event_id)
    )
    result = await session.scalar(stmt)
    return result is not None
