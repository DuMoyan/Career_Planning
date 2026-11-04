from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.assessment import ScaleDefinition, ScoreResult


@dataclass(frozen=True, slots=True)
class AssessmentScaleItem:
    id: UUID
    dimension: str
    prompt: str


@dataclass(frozen=True, slots=True)
class AssessmentScale:
    definition: ScaleDefinition
    name: str
    kind: str
    items: tuple[AssessmentScaleItem, ...]


@dataclass(frozen=True, slots=True)
class AssessmentRecord:
    id: UUID
    student_id: UUID
    scale_id: UUID
    kind: str
    answers: dict[UUID, int]
    score: ScoreResult
    completed_at: datetime
    visibility: str = "private"


class InMemoryAssessmentRepository:
    def __init__(self, scales: list[AssessmentScale]) -> None:
        self.scales = {scale.definition.id: scale for scale in scales}
        self.progress: dict[tuple[UUID, UUID], dict[UUID, int]] = {}
        self.records: dict[UUID, AssessmentRecord] = {}
        self.idempotency: dict[tuple[UUID, str], UUID] = {}

    async def list_scales(self) -> list[AssessmentScale]:
        return list(self.scales.values())

    async def get_scale(self, scale_id: UUID) -> AssessmentScale | None:
        return self.scales.get(scale_id)

    async def save_progress(
        self, student_id: UUID, scale_id: UUID, answers: dict[UUID, int]
    ) -> None:
        self.progress[(student_id, scale_id)] = dict(answers)

    async def get_progress(self, student_id: UUID, scale_id: UUID) -> dict[UUID, int]:
        return dict(self.progress.get((student_id, scale_id), {}))

    async def get_by_idempotency(self, student_id: UUID, key: str) -> AssessmentRecord | None:
        record_id = self.idempotency.get((student_id, key))
        return self.records.get(record_id) if record_id else None

    async def save_record(self, record: AssessmentRecord, key: str) -> None:
        self.records[record.id] = record
        self.idempotency[(record.student_id, key)] = record.id

    async def get_record(self, record_id: UUID) -> AssessmentRecord | None:
        return self.records.get(record_id)
