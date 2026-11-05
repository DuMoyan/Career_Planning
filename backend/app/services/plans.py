from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from app.core.errors import ConflictError, ForbiddenError
from app.domain.plans import PlanStatus, activate_version, ensure_editable
from app.repositories.plans import PlanVersionRecord
from app.repositories.tasks import GrowthTaskRecord, TaskStatus


class PlanService:
    def __init__(self, plans, tasks) -> None:
        self.plans = plans
        self.tasks = tasks

    async def create_draft(
        self,
        student_id: UUID,
        ai_run_id: UUID,
        snapshot,
        *,
        career_plan_id: UUID | None = None,
        parent_version_id: UUID | None = None,
        goal_reference: str | None = None,
    ) -> PlanVersionRecord:
        career_plan_id = career_plan_id or (
            uuid5(NAMESPACE_URL, f"career-plan/{student_id}/{goal_reference}")
            if goal_reference
            else uuid4()
        )
        record = PlanVersionRecord(
            id=uuid4(),
            career_plan_id=career_plan_id,
            student_id=student_id,
            ai_run_id=ai_run_id,
            version=await self.plans.next_version(career_plan_id),
            status=PlanStatus.draft,
            snapshot=snapshot.model_copy(deep=True),
            parent_version_id=parent_version_id,
        )
        await self.plans.save(record)
        return record

    async def activate(
        self, student_id: UUID, version_id: UUID, idempotency_key: str
    ) -> PlanVersionRecord:
        async with self.plans.lock:
            existing = await self.plans.idempotent_version(student_id, idempotency_key)
            if existing:
                return existing
            version = await self._owned(student_id, version_id)
            siblings = await self.plans.list_career_plan(version.career_plan_id)
            activated = activate_version(
                version.to_state(), [item.to_state() for item in siblings if item.id != version.id]
            )
            version.status = activated.status
            version.activated_at = datetime.now(UTC)
            await self._create_snapshot_tasks(version)
            await self.plans.save(version)
            await self.plans.remember_idempotency(student_id, idempotency_key, version.id)
            return version

    async def create_replan(
        self, student_id: UUID, active_version_id: UUID, ai_run_id: UUID, snapshot
    ) -> PlanVersionRecord:
        active = await self._owned(student_id, active_version_id)
        if active.status is not PlanStatus.active:
            raise ConflictError("只能基于当前激活版本发起重规划")
        return await self.create_draft(
            student_id,
            ai_run_id,
            snapshot,
            career_plan_id=active.career_plan_id,
            parent_version_id=active.id,
        )

    async def preview_replan(self, student_id: UUID, draft_id: UUID) -> list[dict]:
        draft = await self._owned(student_id, draft_id)
        ensure_editable(draft.to_state())
        if draft.parent_version_id is None:
            raise ConflictError("该草稿不是重规划版本")
        tasks = await self.tasks.list_for_version(draft.parent_version_id)
        return [
            {
                "task_id": task.id,
                "title": task.title,
                "status": task.status,
                "recommended_action": (
                    "history" if task.status is TaskStatus.completed else "continue"
                ),
            }
            for task in tasks
        ]

    async def activate_replan(
        self,
        student_id: UUID,
        draft_id: UUID,
        migrations: dict[UUID, str],
        idempotency_key: str,
    ) -> PlanVersionRecord:
        async with self.plans.lock:
            existing = await self.plans.idempotent_version(student_id, idempotency_key)
            if existing:
                return existing
            draft = await self._owned(student_id, draft_id)
            ensure_editable(draft.to_state())
            if draft.parent_version_id is None:
                raise ConflictError("该草稿不是重规划版本")
            previous = await self._owned(student_id, draft.parent_version_id)
            if previous.status is not PlanStatus.active:
                raise ConflictError("原计划已不是当前激活版本")
            if any(
                action not in {"continue", "replace", "cancel"} for action in migrations.values()
            ):
                raise ConflictError("任务迁移选择无效")
            previous.status = PlanStatus.archived
            draft.status = PlanStatus.active
            draft.activated_at = datetime.now(UTC)
            await self._create_snapshot_tasks(draft)
            for old_task in await self.tasks.list_for_version(previous.id):
                action = migrations.get(old_task.id, "cancel")
                if action == "continue" and old_task.status is not TaskStatus.completed:
                    await self.tasks.save(
                        GrowthTaskRecord(
                            id=uuid4(),
                            student_id=student_id,
                            plan_version_id=draft.id,
                            title=old_task.title,
                            competency_code=old_task.competency_code,
                            due_date=old_task.due_date,
                            weekly_hours=old_task.weekly_hours,
                            source_refs=list(old_task.source_refs),
                            status=old_task.status,
                            source_task_id=old_task.id,
                        )
                    )
            await self.plans.save(previous)
            await self.plans.save(draft)
            await self.plans.remember_idempotency(student_id, idempotency_key, draft.id)
            return draft

    async def history(self, student_id: UUID) -> list[PlanVersionRecord]:
        return sorted(
            await self.plans.list_student(student_id), key=lambda item: item.version, reverse=True
        )

    async def _owned(self, student_id: UUID, version_id: UUID) -> PlanVersionRecord:
        item = await self.plans.get(version_id)
        if item is None or item.student_id != student_id:
            raise ForbiddenError("计划版本不存在或无权访问")
        return item

    async def _create_snapshot_tasks(self, version: PlanVersionRecord) -> None:
        if await self.tasks.list_for_version(version.id):
            return
        for task in version.snapshot.tasks:
            await self.tasks.save(
                GrowthTaskRecord(
                    id=uuid4(),
                    student_id=version.student_id,
                    plan_version_id=version.id,
                    title=task.title,
                    competency_code=task.competency_code,
                    due_date=task.due_date,
                    weekly_hours=task.weekly_hours,
                    source_refs=list(task.source_refs),
                )
            )

    async def get(self, student_id: UUID, version_id: UUID) -> PlanVersionRecord:
        return await self._owned(student_id, version_id)

    async def update_draft(self, student_id: UUID, version_id: UUID, snapshot) -> PlanVersionRecord:
        version = await self._owned(student_id, version_id)
        ensure_editable(version.to_state())
        version.snapshot = snapshot.model_copy(deep=True)
        await self.plans.save(version)
        return version

    async def discard(self, student_id: UUID, version_id: UUID) -> PlanVersionRecord:
        version = await self._owned(student_id, version_id)
        ensure_editable(version.to_state())
        version.status = PlanStatus.discarded
        await self.plans.save(version)
        return version
