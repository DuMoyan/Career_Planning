from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.errors import ForbiddenError
from app.domain.assessment import score_scale
from app.repositories.assessments import (
    AssessmentRecord,
    AssessmentScale,
    InMemoryAssessmentRepository,
)


class AssessmentService:
    def __init__(self, repository: InMemoryAssessmentRepository) -> None:
        self.repository = repository

    async def list_scales(self) -> list[AssessmentScale]:
        return await self.repository.list_scales()

    async def get_scale(self, scale_id: UUID) -> AssessmentScale:
        scale = await self.repository.get_scale(scale_id)
        if scale is None:
            raise ForbiddenError("测评量表不存在或不可用")
        return scale

    async def save_progress(
        self, student_id: UUID, scale_id: UUID, answers: dict[UUID, int]
    ) -> None:
        await self.get_scale(scale_id)
        await self.repository.save_progress(student_id, scale_id, answers)

    async def get_progress(self, student_id: UUID, scale_id: UUID) -> dict[UUID, int]:
        await self.get_scale(scale_id)
        return await self.repository.get_progress(student_id, scale_id)

    async def submit(self, student_id: UUID, scale_id: UUID, key: str) -> AssessmentRecord:
        existing = await self.repository.get_by_idempotency(student_id, key)
        if existing is not None:
            return existing
        scale = await self.get_scale(scale_id)
        answers = await self.repository.get_progress(student_id, scale_id)
        record = AssessmentRecord(
            id=uuid4(),
            student_id=student_id,
            scale_id=scale_id,
            kind=scale.kind,
            answers=answers,
            score=score_scale(scale.definition, answers),
            completed_at=datetime.now(UTC),
        )
        await self.repository.save_record(record, key)
        return record

    async def get_record(self, student_id: UUID, record_id: UUID) -> AssessmentRecord:
        record = await self.repository.get_record(record_id)
        if record is None or record.student_id != student_id:
            raise ForbiddenError("无权访问该测评记录")
        return record
