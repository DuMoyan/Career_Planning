from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID


class TaskStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


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
    status: TaskStatus = TaskStatus.pending
    source_task_id: UUID | None = None


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self.tasks: dict[UUID, GrowthTaskRecord] = {}

    async def save(self, task: GrowthTaskRecord) -> None:
        self.tasks[task.id] = task

    async def list_for_version(self, version_id: UUID) -> list[GrowthTaskRecord]:
        return [item for item in self.tasks.values() if item.plan_version_id == version_id]
