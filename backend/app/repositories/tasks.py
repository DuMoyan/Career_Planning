import asyncio
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.tasks import TaskStatus
from app.models.task import GrowthTask, TaskCheckIn


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

    async def list_student_checkins(self, student_id: UUID) -> list[TaskCheckInRecord]:
        return [item for item in self.checkins.values() if item.student_id == student_id]


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lock = asyncio.Lock()

    async def save(self, task: GrowthTaskRecord) -> None:
        model = await self.session.get(GrowthTask, task.id)
        if model is None:
            model = GrowthTask(
                id=task.id,
                student_id=task.student_id,
                plan_version_id=task.plan_version_id,
            )
            self.session.add(model)
        model.source_task_id = task.source_task_id
        model.title = task.title
        model.competency_code = task.competency_code
        model.due_date = task.due_date
        model.weekly_hours = task.weekly_hours
        model.source_refs = task.source_refs
        model.status = task.status.value
        model.status_reason = task.status_reason
        await self.session.commit()

    async def list_for_version(self, version_id: UUID) -> list[GrowthTaskRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(GrowthTask).where(GrowthTask.plan_version_id == version_id)
                )
            ).all()
        )
        return [_task_record(model) for model in models]

    async def get(self, task_id: UUID) -> GrowthTaskRecord | None:
        model = await self.session.get(GrowthTask, task_id)
        return _task_record(model) if model is not None else None

    async def list_student(self, student_id: UUID) -> list[GrowthTaskRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(GrowthTask).where(GrowthTask.student_id == student_id)
                )
            ).all()
        )
        return [_task_record(model) for model in models]

    async def save_checkin(self, checkin: TaskCheckInRecord, idempotency_key: str) -> None:
        existing = await self.get_checkin_by_key(checkin.student_id, idempotency_key)
        if existing is not None:
            return
        self.session.add(
            TaskCheckIn(
                id=checkin.id,
                student_id=checkin.student_id,
                task_id=checkin.task_id,
                content=checkin.content,
                actual_hours=checkin.actual_hours,
                proof_url=checkin.proof_url,
                idempotency_key=idempotency_key,
                created_at=checkin.created_at,
            )
        )
        await self.session.commit()

    async def get_checkin_by_key(
        self, student_id: UUID, idempotency_key: str
    ) -> TaskCheckInRecord | None:
        model = await self.session.scalar(
            select(TaskCheckIn).where(
                TaskCheckIn.student_id == student_id,
                TaskCheckIn.idempotency_key == idempotency_key,
            )
        )
        return _checkin_record(model) if model is not None else None

    async def list_checkins(self, task_id: UUID) -> list[TaskCheckInRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(TaskCheckIn)
                    .where(TaskCheckIn.task_id == task_id)
                    .order_by(TaskCheckIn.created_at)
                )
            ).all()
        )
        return [_checkin_record(model) for model in models]

    async def list_student_checkins(self, student_id: UUID) -> list[TaskCheckInRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(TaskCheckIn).where(TaskCheckIn.student_id == student_id)
                )
            ).all()
        )
        return [_checkin_record(model) for model in models]


def _task_record(model: GrowthTask) -> GrowthTaskRecord:
    return GrowthTaskRecord(
        id=model.id,
        student_id=model.student_id,
        plan_version_id=model.plan_version_id,
        source_task_id=model.source_task_id,
        title=model.title,
        competency_code=model.competency_code,
        due_date=model.due_date,
        weekly_hours=model.weekly_hours,
        source_refs=list(model.source_refs),
        status=TaskStatus(model.status),
        status_reason=model.status_reason,
    )


def _checkin_record(model: TaskCheckIn) -> TaskCheckInRecord:
    return TaskCheckInRecord(
        id=model.id,
        student_id=model.student_id,
        task_id=model.task_id,
        content=model.content,
        actual_hours=model.actual_hours,
        proof_url=model.proof_url,
        created_at=model.created_at,
    )
