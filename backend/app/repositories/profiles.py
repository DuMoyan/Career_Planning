from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile


@dataclass(slots=True)
class StudentProfileRecord:
    student_id: UUID
    department: str | None = None
    major: str | None = None
    grade_level: str | None = None
    gpa: float | None = None
    available_hours: float = 0
    constraints: dict[str, Any] = field(default_factory=dict)


class ProfileRepository(Protocol):
    async def get(self, student_id: UUID) -> StudentProfileRecord | None: ...
    async def save(self, profile: StudentProfileRecord) -> None: ...


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, StudentProfileRecord] = {}

    async def get(self, student_id: UUID) -> StudentProfileRecord | None:
        return self._records.get(student_id)

    async def save(self, profile: StudentProfileRecord) -> None:
        self._records[profile.student_id] = profile


class SqlAlchemyProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, student_id: UUID) -> StudentProfileRecord | None:
        model = await self.session.get(StudentProfile, student_id)
        if model is None:
            return None
        return StudentProfileRecord(
            student_id=model.student_id,
            department=model.department,
            major=model.major,
            grade_level=model.grade_level,
            gpa=model.gpa,
            available_hours=model.available_hours,
            constraints=model.constraints,
        )

    async def save(self, profile: StudentProfileRecord) -> None:
        model = await self.session.get(StudentProfile, profile.student_id)
        if model is None:
            model = StudentProfile(student_id=profile.student_id)
            self.session.add(model)
        model.department = profile.department
        model.major = profile.major
        model.grade_level = profile.grade_level
        model.gpa = profile.gpa
        model.available_hours = profile.available_hours
        model.constraints = profile.constraints
        await self.session.commit()
