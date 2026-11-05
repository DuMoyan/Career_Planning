from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    actor_id: UUID | None
    target_type: str
    target_id: str | None
    result: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AuditRepository(Protocol):
    async def append(self, event: AuditEvent) -> None: ...


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    async def list_recent(self, limit: int = 100) -> list[AuditEvent]:
        return list(reversed(self.events[-limit:]))


class SqlAlchemyAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, event: AuditEvent) -> None:
        self.session.add(
            AuditLog(
                id=event.id,
                event_type=event.event_type,
                actor_id=event.actor_id,
                target_type=event.target_type,
                target_id=event.target_id,
                result=event.result,
                event_metadata=event.metadata,
                created_at=event.created_at,
            )
        )
        await self.session.commit()

    async def list_recent(self, limit: int = 100) -> list[AuditEvent]:
        models = list(
            (
                await self.session.scalars(
                    select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
                )
            ).all()
        )
        return [
            AuditEvent(
                id=item.id,
                event_type=item.event_type,
                actor_id=item.actor_id,
                target_type=item.target_type,
                target_id=item.target_id,
                result=item.result,
                metadata=item.event_metadata,
                created_at=item.created_at,
            )
            for item in models
        ]
