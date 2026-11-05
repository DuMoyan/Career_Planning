import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.plans import PlanStatus, PlanVersionState
from app.models.plan import CareerPlan, PlanActivationRequest, PlanVersion
from app.schemas.planning import PlanDraft


@dataclass(slots=True)
class PlanVersionRecord:
    id: UUID
    career_plan_id: UUID
    student_id: UUID
    ai_run_id: UUID
    version: int
    status: PlanStatus
    snapshot: PlanDraft
    parent_version_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    activated_at: datetime | None = None

    def to_state(self) -> PlanVersionState:
        return PlanVersionState(
            id=self.id,
            career_plan_id=self.career_plan_id,
            version=self.version,
            status=self.status,
        )


class InMemoryPlanRepository:
    def __init__(self) -> None:
        self.versions: dict[UUID, PlanVersionRecord] = {}
        self.idempotency: dict[tuple[UUID, str], UUID] = {}
        self.lock = asyncio.Lock()

    async def save(self, version: PlanVersionRecord) -> None:
        self.versions[version.id] = version

    async def get(self, version_id: UUID) -> PlanVersionRecord | None:
        return self.versions.get(version_id)

    async def list_student(self, student_id: UUID) -> list[PlanVersionRecord]:
        return [item for item in self.versions.values() if item.student_id == student_id]

    async def list_career_plan(self, career_plan_id: UUID) -> list[PlanVersionRecord]:
        return [item for item in self.versions.values() if item.career_plan_id == career_plan_id]

    async def next_version(self, career_plan_id: UUID) -> int:
        items = await self.list_career_plan(career_plan_id)
        return max((item.version for item in items), default=0) + 1

    async def idempotent_version(self, student_id: UUID, key: str) -> PlanVersionRecord | None:
        version_id = self.idempotency.get((student_id, key))
        return self.versions.get(version_id) if version_id else None

    async def remember_idempotency(self, student_id: UUID, key: str, version_id: UUID) -> None:
        self.idempotency[(student_id, key)] = version_id


class SqlAlchemyPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lock = asyncio.Lock()

    async def save(self, version: PlanVersionRecord) -> None:
        career_plan = await self.session.get(CareerPlan, version.career_plan_id)
        if career_plan is None:
            self.session.add(
                CareerPlan(id=version.career_plan_id, student_id=version.student_id)
            )
            await self.session.flush()
        model = await self.session.get(PlanVersion, version.id)
        if model is None:
            model = PlanVersion(
                id=version.id,
                career_plan_id=version.career_plan_id,
                ai_run_id=version.ai_run_id,
                version=version.version,
                status=version.status.value,
                snapshot=version.snapshot.model_dump(mode="json"),
            )
            self.session.add(model)
        model.parent_version_id = version.parent_version_id
        model.status = version.status.value
        model.snapshot = version.snapshot.model_dump(mode="json")
        model.created_at = version.created_at
        model.activated_at = version.activated_at
        await self.session.commit()

    async def get(self, version_id: UUID) -> PlanVersionRecord | None:
        model = await self.session.get(PlanVersion, version_id)
        return await self._to_record(model) if model is not None else None

    async def list_student(self, student_id: UUID) -> list[PlanVersionRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(PlanVersion)
                    .join(CareerPlan, CareerPlan.id == PlanVersion.career_plan_id)
                    .where(CareerPlan.student_id == student_id)
                )
            ).all()
        )
        return [await self._to_record(model) for model in models]

    async def list_career_plan(self, career_plan_id: UUID) -> list[PlanVersionRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(PlanVersion).where(PlanVersion.career_plan_id == career_plan_id)
                )
            ).all()
        )
        return [await self._to_record(model) for model in models]

    async def next_version(self, career_plan_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(PlanVersion.version)).where(
                PlanVersion.career_plan_id == career_plan_id
            )
        )
        return int(current or 0) + 1

    async def idempotent_version(self, student_id: UUID, key: str) -> PlanVersionRecord | None:
        request = await self.session.scalar(
            select(PlanActivationRequest).where(
                PlanActivationRequest.student_id == student_id,
                PlanActivationRequest.idempotency_key == key,
            )
        )
        return await self.get(request.version_id) if request is not None else None

    async def remember_idempotency(self, student_id: UUID, key: str, version_id: UUID) -> None:
        existing = await self.session.scalar(
            select(PlanActivationRequest).where(
                PlanActivationRequest.student_id == student_id,
                PlanActivationRequest.idempotency_key == key,
            )
        )
        if existing is None:
            self.session.add(
                PlanActivationRequest(
                    student_id=student_id,
                    idempotency_key=key,
                    version_id=version_id,
                )
            )
            await self.session.commit()

    async def _to_record(self, model: PlanVersion) -> PlanVersionRecord:
        career_plan = await self.session.get(CareerPlan, model.career_plan_id)
        if career_plan is None:
            raise RuntimeError("计划版本缺少职业计划")
        return PlanVersionRecord(
            id=model.id,
            career_plan_id=model.career_plan_id,
            student_id=career_plan.student_id,
            ai_run_id=model.ai_run_id,
            version=model.version,
            status=PlanStatus(model.status),
            snapshot=PlanDraft.model_validate(model.snapshot),
            parent_version_id=model.parent_version_id,
            created_at=model.created_at,
            activated_at=model.activated_at,
        )
