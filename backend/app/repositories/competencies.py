from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.competency import CompetencyProfileSnapshot, ConfirmedEvidence


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
