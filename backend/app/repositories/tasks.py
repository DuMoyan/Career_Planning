import asyncio
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID

from app.domain.tasks import TaskStatus


@dataclass(slots=True)
class GrowthTaskRecord:
    id: UUID
    student_id: UUID
    plan_version_id: UUID
    title: str
    competency_code: str
    due_date: date
    weekly_hours: float
    source_refs: list[str]
    status: TaskStatus = TaskStatus.todo
    status_reason: str | None = None
    source_task_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class TaskCheckInRecord:
    id: UUID
    student_id: UUID
    task_id: UUID
    content: str
    actual_hours: float
    proof_url: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self.tasks: dict[UUID, GrowthTaskRecord] = {}
        self.checkins: dict[UUID, TaskCheckInRecord] = {}
        self.idempotency: dict[tuple[UUID, str], UUID] = {}
        self.lock = asyncio.Lock()

    async def save(self, task: GrowthTaskRecord) -> None:
        self.tasks[task.id] = task

    async def list_for_version(self, version_id: UUID) -> list[GrowthTaskRecord]:
        return [item for item in self.tasks.values() if item.plan_version_id == version_id]

    async def get(self, task_id: UUID) -> GrowthTaskRecord | None:
        return self.tasks.get(task_id)

    async def list_student(self, student_id: UUID) -> list[GrowthTaskRecord]:
        return [item for item in self.tasks.values() if item.student_id == student_id]

    async def save_checkin(self, checkin: TaskCheckInRecord, idempotency_key: str) -> None:
        self.checkins[checkin.id] = checkin
        self.idempotency[(checkin.student_id, idempotency_key)] = checkin.id

    async def get_checkin_by_key(
        self, student_id: UUID, idempotency_key: str
    ) -> TaskCheckInRecord | None:
        checkin_id = self.idempotency.get((student_id, idempotency_key))
        return self.checkins.get(checkin_id) if checkin_id else None

    async def list_checkins(self, task_id: UUID) -> list[TaskCheckInRecord]:
        return [item for item in self.checkins.values() if item.task_id == task_id]
