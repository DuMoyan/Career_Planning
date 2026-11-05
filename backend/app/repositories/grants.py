from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.grants import GrantScope, MentorGrant
from app.models.mentor import MentorGrantModel


class GrantRepository(Protocol):
    async def save(self, grant: MentorGrant) -> None: ...
    async def get(self, grant_id: UUID) -> MentorGrant | None: ...
    async def find_active(self, mentor_id: UUID, student_id: UUID) -> MentorGrant | None: ...
    async def list_mentor(self, mentor_id: UUID) -> list[MentorGrant]: ...


@dataclass(frozen=True, slots=True)
class CachedGrantDecision:
    allowed: bool
    expires_at: datetime


class GrantCache(Protocol):
    async def get(
        self, mentor_id: UUID, student_id: UUID, scope: GrantScope
    ) -> CachedGrantDecision | None: ...
    async def set(
        self,
        mentor_id: UUID,
        student_id: UUID,
        scope: GrantScope,
        allowed: bool,
        expires_at: datetime,
    ) -> None: ...
    async def invalidate(self, mentor_id: UUID, student_id: UUID) -> None: ...


class InMemoryGrantRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, MentorGrant] = {}

    async def save(self, grant: MentorGrant) -> None:
        self.records[grant.id] = grant

    async def get(self, grant_id: UUID) -> MentorGrant | None:
        return self.records.get(grant_id)

    async def find_active(self, mentor_id: UUID, student_id: UUID) -> MentorGrant | None:
        return next(
            (
                grant
                for grant in self.records.values()
                if grant.mentor_id == mentor_id and grant.student_id == student_id
            ),
            None,
        )

    async def list_mentor(self, mentor_id: UUID) -> list[MentorGrant]:
        return [grant for grant in self.records.values() if grant.mentor_id == mentor_id]


class InMemoryGrantCache:
    def __init__(self) -> None:
        self.values: dict[tuple[UUID, UUID, GrantScope], CachedGrantDecision] = {}

    async def get(
        self, mentor_id: UUID, student_id: UUID, scope: GrantScope
    ) -> CachedGrantDecision | None:
        return self.values.get((mentor_id, student_id, scope))

    async def set(
        self,
        mentor_id: UUID,
        student_id: UUID,
        scope: GrantScope,
        allowed: bool,
        expires_at: datetime,
    ) -> None:
        self.values[(mentor_id, student_id, scope)] = CachedGrantDecision(allowed, expires_at)

    async def invalidate(self, mentor_id: UUID, student_id: UUID) -> None:
        keys = [key for key in self.values if key[:2] == (mentor_id, student_id)]
        for key in keys:
            del self.values[key]


class SqlAlchemyGrantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, grant: MentorGrant) -> None:
        model = await self.session.get(MentorGrantModel, grant.id)
        if model is None:
            model = MentorGrantModel(
                id=grant.id,
                student_id=grant.student_id,
                mentor_id=grant.mentor_id,
            )
            self.session.add(model)
        model.scopes = [scope.value for scope in grant.scopes]
        model.expires_at = grant.expires_at
        model.revoked_at = grant.revoked_at
        await self.session.commit()

    async def get(self, grant_id: UUID) -> MentorGrant | None:
        return _grant_from_model(await self.session.get(MentorGrantModel, grant_id))

    async def find_active(self, mentor_id: UUID, student_id: UUID) -> MentorGrant | None:
        model = await self.session.scalar(
            select(MentorGrantModel).where(
                MentorGrantModel.mentor_id == mentor_id,
                MentorGrantModel.student_id == student_id,
            )
        )
        return _grant_from_model(model)

    async def list_mentor(self, mentor_id: UUID) -> list[MentorGrant]:
        models = list(
            (
                await self.session.scalars(
                    select(MentorGrantModel).where(MentorGrantModel.mentor_id == mentor_id)
                )
            ).all()
        )
        return [grant for model in models if (grant := _grant_from_model(model)) is not None]


class RedisGrantCache:
    def __init__(self, redis: Redis, ttl_seconds: int = 300) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def _key(self, mentor_id: UUID, student_id: UUID, scope: GrantScope) -> str:
        return f"grant:{mentor_id}:{student_id}:{scope.value}"

    async def get(
        self, mentor_id: UUID, student_id: UUID, scope: GrantScope
    ) -> CachedGrantDecision | None:
        value = await self.redis.get(self._key(mentor_id, student_id, scope))
        if value is None:
            return None
        raw = value.decode() if isinstance(value, bytes) else value
        allowed, expires_at = raw.split("|", maxsplit=1)
        return CachedGrantDecision(allowed == "1", datetime.fromisoformat(expires_at))

    async def set(
        self,
        mentor_id: UUID,
        student_id: UUID,
        scope: GrantScope,
        allowed: bool,
        expires_at: datetime,
    ) -> None:
        ttl = min(
            self.ttl_seconds,
            max(1, int((expires_at - datetime.now(UTC)).total_seconds())),
        )
        await self.redis.set(
            self._key(mentor_id, student_id, scope),
            f"{'1' if allowed else '0'}|{expires_at.isoformat()}",
            ex=ttl,
        )

    async def invalidate(self, mentor_id: UUID, student_id: UUID) -> None:
        keys = [self._key(mentor_id, student_id, scope) for scope in GrantScope]
        await self.redis.delete(*keys)


def _grant_from_model(model: MentorGrantModel | None) -> MentorGrant | None:
    if model is None:
        return None
    expires_at = model.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    revoked_at = model.revoked_at
    if revoked_at is not None and revoked_at.tzinfo is None:
        revoked_at = revoked_at.replace(tzinfo=UTC)
    return MentorGrant(
        id=model.id,
        student_id=model.student_id,
        mentor_id=model.mentor_id,
        scopes=frozenset(GrantScope(scope) for scope in model.scopes),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )
