from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.errors import ForbiddenError
from app.domain.grants import GrantPolicy, GrantScope, MentorGrant
from app.repositories.audits import AuditEvent, AuditRepository
from app.repositories.grants import GrantCache, GrantRepository


class GrantService:
    def __init__(
        self,
        *,
        repository: GrantRepository,
        cache: GrantCache,
        audits: AuditRepository,
    ) -> None:
        self.repository = repository
        self.cache = cache
        self.audits = audits

    async def create(
        self,
        *,
        student_id: UUID,
        mentor_id: UUID,
        scopes: frozenset[GrantScope],
        expires_at: datetime | None,
    ) -> MentorGrant:
        now = datetime.now(UTC)
        grant = MentorGrant(
            id=uuid4(),
            student_id=student_id,
            mentor_id=mentor_id,
            scopes=scopes,
            expires_at=expires_at or now + timedelta(days=90),
        )
        await self.repository.save(grant)
        await self.cache.invalidate(mentor_id, student_id)
        await self.audits.append(
            AuditEvent(
                event_type="mentor_grant_created",
                actor_id=student_id,
                target_type="mentor_grant",
                target_id=str(grant.id),
                result="success",
            )
        )
        return grant

    async def revoke(self, grant_id: UUID, student_id: UUID) -> None:
        grant = await self.repository.get(grant_id)
        if grant is None or grant.student_id != student_id:
            raise ForbiddenError("无权撤回该授权")
        revoked = replace(grant, revoked_at=datetime.now(UTC))
        await self.repository.save(revoked)
        await self.cache.invalidate(grant.mentor_id, grant.student_id)
        await self.audits.append(
            AuditEvent(
                event_type="mentor_grant_revoked",
                actor_id=student_id,
                target_type="mentor_grant",
                target_id=str(grant.id),
                result="success",
            )
        )

    async def can_read(self, mentor_id: UUID, student_id: UUID, scope: GrantScope) -> bool:
        cached = await self.cache.get(mentor_id, student_id, scope)
        if cached is not None:
            return cached
        grant = await self.repository.find_active(mentor_id, student_id)
        allowed = GrantPolicy.can_read(grant, scope, datetime.now(UTC))
        await self.cache.set(mentor_id, student_id, scope, allowed)
        return allowed
