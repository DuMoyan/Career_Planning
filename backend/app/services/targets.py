from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from app.core.errors import DomainError
from app.domain.competency import calculate_profile
from app.domain.gap import analyze_gap
from app.repositories.targets import GoalRecord


class TargetService:
    def __init__(self, repository, competencies, *, stale_after_days: int = 180) -> None:
        self.repository = repository
        self.competencies = competencies
        self.stale_after_days = stale_after_days

    async def search(self, keyword: str | None, category: str | None):
        return await self.repository.search_targets(keyword, category)

    def is_stale(self, verified_at: date) -> bool:
        return date.today() - verified_at > timedelta(days=self.stale_after_days)

    async def compare(self, student_id: UUID, target_ids: list[UUID]) -> list[dict]:
        evidence = await self.competencies.list_evidence(student_id)
        snapshot = calculate_profile([item.to_domain() for item in evidence])
        profile = {
            code: (dimension.level, dimension.evidence_ids)
            for code, dimension in snapshot.dimensions.items()
        }
        comparisons = []
        for target_id in target_ids:
            target = await self.repository.get_target(target_id)
            if target is None:
                raise DomainError("目标岗位不存在")
            comparisons.append(
                {
                    "target": target,
                    "gaps": analyze_gap(list(target.requirements), profile),
                }
            )
        return comparisons


class GoalService:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def create(self, student_id: UUID, payload) -> GoalRecord:
        if await self.repository.get_target(payload.target_id) is None:
            raise DomainError("目标岗位不存在")
        goal = GoalRecord(
            id=uuid4(),
            student_id=student_id,
            target_id=payload.target_id,
            deadline=payload.deadline,
            weekly_hours=payload.weekly_hours,
            constraints=payload.constraints,
            primary=payload.primary,
            created_at=datetime.now(UTC),
        )
        if goal.primary:
            await self.set_primary(goal)
        else:
            await self.repository.save_goal(goal)
        return goal

    async def set_primary(self, goal: GoalRecord) -> None:
        """持久化层以同一事务撤销旧主目标并设置新主目标。"""
        await self.repository.save_goal(goal)

    async def list(self, student_id: UUID) -> list[GoalRecord]:
        return await self.repository.list_goals(student_id)
