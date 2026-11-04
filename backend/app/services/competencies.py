from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.errors import ForbiddenError
from app.domain.competency import calculate_profile
from app.repositories.competencies import EvidenceRecord, ProfileVersion


class CompetencyService:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def add_evidence(self, student_id: UUID, payload) -> EvidenceRecord:
        if payload.resume_id is not None:
            resume = await self.repository.get_resume(payload.resume_id)
            if resume is None or resume.student_id != student_id or resume.deleted_at is not None:
                raise ForbiddenError("简历来源无效")
        item = EvidenceRecord(
            id=uuid4(),
            student_id=student_id,
            resume_id=payload.resume_id,
            competency_code=payload.competency_code,
            demonstrated_level=payload.demonstrated_level,
            description=payload.description,
        )
        await self.repository.add_evidence(item)
        return item

    async def list_evidence(self, student_id: UUID):
        return await self.repository.list_evidence(student_id)

    async def create_profile(self, student_id: UUID) -> ProfileVersion:
        items = await self.repository.list_evidence(student_id)
        profile = ProfileVersion(
            id=uuid4(),
            student_id=student_id,
            version=await self.repository.next_profile_version(student_id),
            snapshot=calculate_profile([item.to_domain() for item in items]),
            created_at=datetime.now(UTC),
        )
        await self.repository.add_profile(profile)
        return profile
