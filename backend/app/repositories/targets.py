from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.gap import TargetRequirement
from app.models.goal import CareerGoal
from app.models.target import CareerTarget, CareerTargetRequirement


@dataclass(frozen=True, slots=True)
class TargetRecord:
    id: UUID
    code: str
    name: str
    category: str
    description: str
    source: str
    verified_at: date
    interests: tuple[str, ...]
    values: tuple[str, ...]
    requirements: tuple[TargetRequirement, ...]


@dataclass(slots=True)
class GoalRecord:
    id: UUID
    student_id: UUID
    target_id: UUID
    deadline: date
    weekly_hours: int | None
    constraints: str | None
    primary: bool
    created_at: datetime


class InMemoryTargetRepository:
    def __init__(self, targets: list[TargetRecord] | None = None) -> None:
        self.targets = {item.id: item for item in targets or []}
        self.goals: dict[UUID, GoalRecord] = {}

    async def search_targets(
        self, keyword: str | None = None, category: str | None = None
    ) -> list[TargetRecord]:
        normalized = (keyword or "").strip().lower()
        return [
            item
            for item in self.targets.values()
            if (not normalized or normalized in f"{item.name} {item.description}".lower())
            and (not category or item.category == category)
        ]

    async def get_target(self, target_id: UUID) -> TargetRecord | None:
        return self.targets.get(target_id)

    async def save_goal(self, goal: GoalRecord) -> None:
        if goal.primary:
            for existing in self.goals.values():
                if existing.student_id == goal.student_id:
                    existing.primary = False
        self.goals[goal.id] = goal

    async def list_goals(self, student_id: UUID) -> list[GoalRecord]:
        return [item for item in self.goals.values() if item.student_id == student_id]


class SqlAlchemyTargetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_targets(
        self, keyword: str | None = None, category: str | None = None
    ) -> list[TargetRecord]:
        statement = select(CareerTarget)
        if keyword and keyword.strip():
            pattern = f"%{keyword.strip()}%"
            statement = statement.where(
                CareerTarget.name.ilike(pattern) | CareerTarget.description.ilike(pattern)
            )
        if category:
            statement = statement.where(CareerTarget.category == category)
        models = list((await self.session.scalars(statement.order_by(CareerTarget.name))).all())
        return [await self._target_record(model) for model in models]

    async def get_target(self, target_id: UUID) -> TargetRecord | None:
        model = await self.session.get(CareerTarget, target_id)
        return await self._target_record(model) if model is not None else None

    async def save_goal(self, goal: GoalRecord) -> None:
        if goal.primary:
            await self.session.execute(
                update(CareerGoal)
                .where(CareerGoal.student_id == goal.student_id, CareerGoal.id != goal.id)
                .values(primary=False)
            )
        model = await self.session.get(CareerGoal, goal.id)
        if model is None:
            model = CareerGoal(id=goal.id, student_id=goal.student_id, target_id=goal.target_id)
            self.session.add(model)
        model.deadline = goal.deadline
        model.weekly_hours = goal.weekly_hours
        model.constraints = goal.constraints
        model.primary = goal.primary
        model.created_at = goal.created_at
        await self.session.commit()

    async def list_goals(self, student_id: UUID) -> list[GoalRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(CareerGoal)
                    .where(CareerGoal.student_id == student_id)
                    .order_by(CareerGoal.created_at)
                )
            ).all()
        )
        return [
            GoalRecord(
                id=model.id,
                student_id=model.student_id,
                target_id=model.target_id,
                deadline=model.deadline,
                weekly_hours=model.weekly_hours,
                constraints=model.constraints,
                primary=model.primary,
                created_at=model.created_at,
            )
            for model in models
        ]

    async def _target_record(self, model: CareerTarget) -> TargetRecord:
        requirements = list(
            (
                await self.session.scalars(
                    select(CareerTargetRequirement).where(
                        CareerTargetRequirement.target_id == model.id
                    )
                )
            ).all()
        )
        return TargetRecord(
            id=model.id,
            code=model.code,
            name=model.name,
            category=model.category,
            description=model.description,
            source=model.source,
            verified_at=model.verified_at,
            interests=tuple(model.interests),
            values=tuple(model.values),
            requirements=tuple(
                TargetRequirement(
                    id=item.id,
                    competency_code=item.competency_code,
                    required_level=item.required_level,
                    hard=item.hard,
                    source=item.source,
                    verified_at=item.verified_at.isoformat(),
                )
                for item in requirements
            ),
        )
