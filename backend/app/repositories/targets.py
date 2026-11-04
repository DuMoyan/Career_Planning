from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.domain.gap import TargetRequirement


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
