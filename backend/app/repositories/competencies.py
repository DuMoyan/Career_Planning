from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.competency import (
    CompetencyDimension,
    CompetencyProfileSnapshot,
    ConfirmedEvidence,
)
from app.models.competency import CompetencyEvidence, CompetencyProfile
from app.models.resume import ResumeFile


@dataclass(frozen=True, slots=True)
class ResumeCandidate:
    competency_code: str
    description: str


@dataclass(slots=True)
class ResumeDraft:
    id: UUID
    student_id: UUID
    file_key: str
    file_name: str
    media_type: str
    candidates: tuple[ResumeCandidate, ...]
    deleted_at: datetime | None = None


@dataclass(slots=True)
class EvidenceRecord:
    id: UUID
    student_id: UUID
    resume_id: UUID | None
    competency_code: str
    demonstrated_level: int
    description: str
    source_type: str = "resume"
    source_deleted: bool = False

    def to_domain(self) -> ConfirmedEvidence:
        return ConfirmedEvidence(
            id=self.id,
            competency_code=self.competency_code,
            demonstrated_level=self.demonstrated_level,
            confirmed=True,
            deleted=False,
            source_type=self.source_type,
        )


@dataclass(frozen=True, slots=True)
class ProfileVersion:
    id: UUID
    student_id: UUID
    version: int
    snapshot: CompetencyProfileSnapshot
    created_at: datetime


class InMemoryCompetencyRepository:
    def __init__(self) -> None:
        self.resumes: dict[UUID, ResumeDraft] = {}
        self.evidence: dict[UUID, EvidenceRecord] = {}
        self.profiles: list[ProfileVersion] = []

    async def save_resume(self, resume: ResumeDraft) -> None:
        self.resumes[resume.id] = resume

    async def get_resume(self, resume_id: UUID) -> ResumeDraft | None:
        return self.resumes.get(resume_id)

    async def delete_resume(self, resume_id: UUID, student_id: UUID) -> ResumeDraft | None:
        resume = self.resumes.get(resume_id)
        if resume is None or resume.student_id != student_id:
            return None
        resume.deleted_at = datetime.now(UTC)
        for item in self.evidence.values():
            if item.resume_id == resume_id:
                item.source_deleted = True
        return resume

    async def add_evidence(self, item: EvidenceRecord) -> None:
        self.evidence[item.id] = item

    async def list_evidence(self, student_id: UUID) -> list[EvidenceRecord]:
        return [item for item in self.evidence.values() if item.student_id == student_id]

    async def add_profile(self, profile: ProfileVersion) -> None:
        self.profiles.append(profile)

    async def next_profile_version(self, student_id: UUID) -> int:
        return 1 + sum(profile.student_id == student_id for profile in self.profiles)


class SqlAlchemyCompetencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_resume(self, resume: ResumeDraft) -> None:
        model = await self.session.get(ResumeFile, resume.id)
        if model is None:
            model = ResumeFile(
                id=resume.id,
                student_id=resume.student_id,
                file_key=resume.file_key,
                file_name=resume.file_name,
                media_type=resume.media_type,
            )
            self.session.add(model)
        model.candidates = [
            {
                "competency_code": item.competency_code,
                "description": item.description,
            }
            for item in resume.candidates
        ]
        model.deleted_at = resume.deleted_at
        await self.session.commit()

    async def get_resume(self, resume_id: UUID) -> ResumeDraft | None:
        model = await self.session.get(ResumeFile, resume_id)
        if model is None:
            return None
        return ResumeDraft(
            id=model.id,
            student_id=model.student_id,
            file_key=model.file_key,
            file_name=model.file_name,
            media_type=model.media_type,
            candidates=tuple(ResumeCandidate(**item) for item in model.candidates),
            deleted_at=model.deleted_at,
        )

    async def delete_resume(self, resume_id: UUID, student_id: UUID) -> ResumeDraft | None:
        resume = await self.get_resume(resume_id)
        if resume is None or resume.student_id != student_id:
            return None
        resume.deleted_at = datetime.now(UTC)
        model = await self.session.get(ResumeFile, resume_id)
        if model is None:
            return None
        model.deleted_at = resume.deleted_at
        await self.session.execute(
            update(CompetencyEvidence)
            .where(CompetencyEvidence.resume_id == resume_id)
            .values(source_deleted=True)
        )
        await self.session.commit()
        return resume

    async def add_evidence(self, item: EvidenceRecord) -> None:
        self.session.add(
            CompetencyEvidence(
                id=item.id,
                student_id=item.student_id,
                resume_id=item.resume_id,
                competency_code=item.competency_code,
                demonstrated_level=item.demonstrated_level,
                description=item.description,
                source_type=item.source_type,
                source_deleted=item.source_deleted,
                confirmed=True,
            )
        )
        await self.session.commit()

    async def list_evidence(self, student_id: UUID) -> list[EvidenceRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(CompetencyEvidence)
                    .where(CompetencyEvidence.student_id == student_id)
                    .order_by(CompetencyEvidence.created_at)
                )
            ).all()
        )
        return [
            EvidenceRecord(
                id=model.id,
                student_id=model.student_id,
                resume_id=model.resume_id,
                competency_code=model.competency_code,
                demonstrated_level=model.demonstrated_level,
                description=model.description,
                source_type=model.source_type,
                source_deleted=model.source_deleted,
            )
            for model in models
        ]

    async def add_profile(self, profile: ProfileVersion) -> None:
        self.session.add(
            CompetencyProfile(
                id=profile.id,
                student_id=profile.student_id,
                version=profile.version,
                dimensions={
                    code: {
                        "level": item.level,
                        "evidence_count": item.evidence_count,
                        "evidence_ids": [str(value) for value in item.evidence_ids],
                        "source_types": list(item.source_types),
                    }
                    for code, item in profile.snapshot.dimensions.items()
                },
                data_completeness=profile.snapshot.data_completeness,
                created_at=profile.created_at,
            )
        )
        await self.session.commit()

    async def next_profile_version(self, student_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(CompetencyProfile.version)).where(
                CompetencyProfile.student_id == student_id
            )
        )
        return int(current or 0) + 1

    async def latest_profile(self, student_id: UUID) -> ProfileVersion | None:
        model = await self.session.scalar(
            select(CompetencyProfile)
            .where(CompetencyProfile.student_id == student_id)
            .order_by(CompetencyProfile.version.desc())
            .limit(1)
        )
        if model is None:
            return None
        dimensions = {
            code: CompetencyDimension(
                level=item["level"],
                evidence_count=item["evidence_count"],
                evidence_ids=tuple(UUID(value) for value in item["evidence_ids"]),
                source_types=tuple(item["source_types"]),
            )
            for code, item in model.dimensions.items()
        }
        return ProfileVersion(
            id=model.id,
            student_id=model.student_id,
            version=model.version,
            snapshot=CompetencyProfileSnapshot(dimensions, model.data_completeness),
            created_at=model.created_at,
        )
