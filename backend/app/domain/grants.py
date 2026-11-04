from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class GrantScope(StrEnum):
    profile_summary = "profile_summary"
    goals = "goals"
    plan_progress = "plan_progress"


@dataclass(frozen=True, slots=True)
class MentorGrant:
    id: UUID
    student_id: UUID
    mentor_id: UUID
    scopes: frozenset[GrantScope]
    expires_at: datetime
    revoked_at: datetime | None = None


class GrantPolicy:
    @staticmethod
    def can_read(
        grant: MentorGrant | None,
        scope: GrantScope,
        now: datetime,
    ) -> bool:
        return bool(
            grant is not None
            and grant.revoked_at is None
            and grant.expires_at > now
            and scope in grant.scopes
        )
