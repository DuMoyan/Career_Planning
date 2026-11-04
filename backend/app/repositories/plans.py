import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.domain.plans import PlanStatus, PlanVersionState
from app.schemas.planning import PlanDraft


@dataclass(slots=True)
class PlanVersionRecord:
    id: UUID
    career_plan_id: UUID
    student_id: UUID
    ai_run_id: UUID
    version: int
    status: PlanStatus
    snapshot: PlanDraft
    parent_version_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    activated_at: datetime | None = None

    def to_state(self) -> PlanVersionState:
        return PlanVersionState(
            id=self.id,
            career_plan_id=self.career_plan_id,
            version=self.version,
            status=self.status,
        )


class InMemoryPlanRepository:
    def __init__(self) -> None:
        self.versions: dict[UUID, PlanVersionRecord] = {}
        self.idempotency: dict[tuple[UUID, str], UUID] = {}
        self.lock = asyncio.Lock()

    async def save(self, version: PlanVersionRecord) -> None:
        self.versions[version.id] = version

    async def get(self, version_id: UUID) -> PlanVersionRecord | None:
        return self.versions.get(version_id)

    async def list_student(self, student_id: UUID) -> list[PlanVersionRecord]:
        return [item for item in self.versions.values() if item.student_id == student_id]

    async def list_career_plan(self, career_plan_id: UUID) -> list[PlanVersionRecord]:
        return [item for item in self.versions.values() if item.career_plan_id == career_plan_id]

    async def next_version(self, career_plan_id: UUID) -> int:
        items = await self.list_career_plan(career_plan_id)
        return max((item.version for item in items), default=0) + 1

    async def idempotent_version(self, student_id: UUID, key: str) -> PlanVersionRecord | None:
        version_id = self.idempotency.get((student_id, key))
        return self.versions.get(version_id) if version_id else None

    async def remember_idempotency(self, student_id: UUID, key: str, version_id: UUID) -> None:
        self.idempotency[(student_id, key)] = version_id
