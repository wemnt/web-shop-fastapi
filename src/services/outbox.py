from sqlalchemy.ext.asyncio import AsyncSession

from events.schemas import Event
from models.outbox_event import OutboxEvent


class OutboxService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, event: Event) -> None:
        self.session.add(
            OutboxEvent(
                id=event.event_id,
                subject=event.subject,
                payload=event.model_dump(mode="json"),
            )
        )
