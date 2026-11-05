from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_run import AIPlanningRun


@dataclass(slots=True)
class AIRunRecord:
    id: UUID
    student_id: UUID
    status: str
    input_references: dict[str, str]
    plan_snapshot: dict | None = None
    validation_result: dict | None = None
    sources: list[str] = field(default_factory=list)
    generation_mode: str | None = None
    fallback_reason: str | None = None
    service_version: str = "planning-service-1"
    model_version: str = "unavailable"
    prompt_version: str = "planning-prompt-1"
    confirmation_status: str = "pending"
    parent_run_id: UUID | None = None
    error_code: str | None = None
    events: list[tuple[str, dict]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryAIRunRepository:
    def __init__(self) -> None:
        self.runs: dict[UUID, AIRunRecord] = {}

    async def get(self, run_id: UUID) -> AIRunRecord | None:
        return self.runs.get(run_id)

    async def save(self, run: AIRunRecord) -> None:
        run.updated_at = datetime.now(UTC)
        self.runs[run.id] = run

    async def find_running(self, student_id: UUID) -> AIRunRecord | None:
        return next(
            (
                run
                for run in self.runs.values()
                if run.student_id == student_id and run.status in {"queued", "running"}
            ),
            None,
        )


class SqlAlchemyAIRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, run_id: UUID) -> AIRunRecord | None:
        return _to_record(await self.session.get(AIPlanningRun, run_id))

    async def save(self, run: AIRunRecord) -> None:
        model = await self.session.get(AIPlanningRun, run.id)
        if model is None:
            model = AIPlanningRun(id=run.id, student_id=run.student_id)
            self.session.add(model)
        run.updated_at = datetime.now(UTC)
        model.parent_run_id = run.parent_run_id
        model.status = run.status
        model.generation_mode = run.generation_mode
        model.fallback_reason = run.fallback_reason
        model.service_version = run.service_version
        model.model_version = run.model_version
        model.prompt_version = run.prompt_version
        model.input_references = run.input_references
        model.plan_snapshot = run.plan_snapshot
        model.validation_result = run.validation_result
        model.sources = run.sources
        model.confirmation_status = run.confirmation_status
        model.error_code = run.error_code
        model.created_at = run.created_at
        model.updated_at = run.updated_at
        await self.session.commit()

    async def find_running(self, student_id: UUID) -> AIRunRecord | None:
        model = await self.session.scalar(
            select(AIPlanningRun).where(
                AIPlanningRun.student_id == student_id,
                AIPlanningRun.status.in_(("queued", "running")),
            )
        )
        return _to_record(model)


def _to_record(model: AIPlanningRun | None) -> AIRunRecord | None:
    if model is None:
        return None
    events: list[tuple[str, dict]] = [("started", {"status": "running"})]
    if model.status == "completed":
        events.append(
            (
                "completed",
                {
                    "status": "completed",
                    "generation_mode": model.generation_mode,
                    "fallback_reason": model.fallback_reason,
                },
            )
        )
    return AIRunRecord(
        id=model.id,
        student_id=model.student_id,
        parent_run_id=model.parent_run_id,
        status=model.status,
        generation_mode=model.generation_mode,
        fallback_reason=model.fallback_reason,
        service_version=model.service_version,
        model_version=model.model_version,
        prompt_version=model.prompt_version,
        input_references=dict(model.input_references),
        plan_snapshot=model.plan_snapshot,
        validation_result=model.validation_result,
        sources=list(model.sources),
        confirmation_status=model.confirmation_status,
        error_code=model.error_code,
        events=events,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
