from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.assessment import ScaleDefinition, ScaleItem, ScoreResult
from app.models.assessment import (
    AssessmentItemModel,
    AssessmentProgressModel,
    AssessmentRecordModel,
    AssessmentScaleModel,
)


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


class SqlAlchemyAssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_scales(self) -> list[AssessmentScale]:
        models = list((await self.session.scalars(select(AssessmentScaleModel))).all())
        return [await self._scale(model) for model in models]

    async def get_scale(self, scale_id: UUID) -> AssessmentScale | None:
        model = await self.session.get(AssessmentScaleModel, scale_id)
        return await self._scale(model) if model is not None else None

    async def save_progress(
        self, student_id: UUID, scale_id: UUID, answers: dict[UUID, int]
    ) -> None:
        model = await self.session.get(AssessmentProgressModel, (student_id, scale_id))
        if model is None:
            model = AssessmentProgressModel(student_id=student_id, scale_id=scale_id)
            self.session.add(model)
        model.answers = {str(key): value for key, value in answers.items()}
        await self.session.commit()

    async def get_progress(self, student_id: UUID, scale_id: UUID) -> dict[UUID, int]:
        model = await self.session.get(AssessmentProgressModel, (student_id, scale_id))
        if model is None:
            return {}
        return {UUID(key): value for key, value in model.answers.items()}

    async def get_by_idempotency(self, student_id: UUID, key: str) -> AssessmentRecord | None:
        model = await self.session.scalar(
            select(AssessmentRecordModel).where(
                AssessmentRecordModel.student_id == student_id,
                AssessmentRecordModel.idempotency_key == key,
            )
        )
        return await self._record(model) if model is not None else None

    async def save_record(self, record: AssessmentRecord, key: str) -> None:
        self.session.add(
            AssessmentRecordModel(
                id=record.id,
                student_id=record.student_id,
                scale_id=record.scale_id,
                scale_version=record.score.scale_version,
                answers={str(item): value for item, value in record.answers.items()},
                dimension_scores=record.score.dimension_scores,
                visibility=record.visibility,
                idempotency_key=key,
                completed_at=record.completed_at,
            )
        )
        await self.session.commit()

    async def get_record(self, record_id: UUID) -> AssessmentRecord | None:
        model = await self.session.get(AssessmentRecordModel, record_id)
        return await self._record(model) if model is not None else None

    async def _scale(self, model: AssessmentScaleModel) -> AssessmentScale:
        items = list(
            (
                await self.session.scalars(
                    select(AssessmentItemModel)
                    .where(AssessmentItemModel.scale_id == model.id)
                    .order_by(AssessmentItemModel.id)
                )
            ).all()
        )
        scale_items = tuple(
            AssessmentScaleItem(item.id, item.dimension, item.prompt) for item in items
        )
        return AssessmentScale(
            definition=ScaleDefinition(
                id=model.id,
                version=model.version,
                scoring_version=model.scoring_version,
                interpretation_version=model.interpretation_version,
                items=tuple(ScaleItem(item.id, item.dimension) for item in items),
            ),
            name=model.name,
            kind=model.kind,
            items=scale_items,
        )

    async def _record(self, model: AssessmentRecordModel) -> AssessmentRecord:
        scale = await self.get_scale(model.scale_id)
        if scale is None:
            raise RuntimeError("测评记录缺少量表")
        ordered = sorted(
            model.dimension_scores,
            key=lambda dimension: (-model.dimension_scores[dimension], dimension),
        )
        return AssessmentRecord(
            id=model.id,
            student_id=model.student_id,
            scale_id=model.scale_id,
            kind=scale.kind,
            answers={UUID(key): value for key, value in model.answers.items()},
            score=ScoreResult(
                dimension_scores=model.dimension_scores,
                top_dimensions=tuple(ordered[:3]),
                scale_version=model.scale_version,
                scoring_version=scale.definition.scoring_version,
                interpretation_version=scale.definition.interpretation_version,
            ),
            completed_at=model.completed_at,
            visibility=model.visibility,
        )
