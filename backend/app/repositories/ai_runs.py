from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


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
