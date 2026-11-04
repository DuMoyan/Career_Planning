from datetime import date, timedelta
from uuid import UUID, uuid4

from app.core.errors import ConflictError, ForbiddenError
from app.domain.plans import PlanStatus
from app.domain.tasks import TaskState, TaskStatus, transition_task
from app.repositories.tasks import TaskCheckInRecord


class TaskService:
    def __init__(self, tasks, plans) -> None:
        self.tasks = tasks
        self.plans = plans

    async def list(
        self,
        student_id: UUID,
        *,
        week_start: date | None = None,
        status: TaskStatus | None = None,
    ):
        items = await self.tasks.list_student(student_id)
        items = [
            item
            for item in items
            if (await self.plans.get(item.plan_version_id)) is not None
            and (await self.plans.get(item.plan_version_id)).status is PlanStatus.active
        ]
        if week_start:
            week_end = week_start + timedelta(days=7)
            items = [item for item in items if week_start <= item.due_date < week_end]
        if status:
            items = [item for item in items if item.status is status]
        return sorted(items, key=lambda item: (item.due_date, item.title))

    async def transition(
        self,
        student_id: UUID,
        task_id: UUID,
        target: TaskStatus,
        *,
        reason: str | None = None,
    ):
        task = await self._owned(student_id, task_id)
        plan = await self.plans.get(task.plan_version_id)
        if plan is None:
            raise ConflictError("任务所属计划不存在")
        changed = transition_task(
            TaskState(
                id=task.id,
                status=task.status,
                plan_status=plan.status,
                check_in_ids=tuple(item.id for item in await self.tasks.list_checkins(task.id)),
                status_reason=task.status_reason,
            ),
            target,
            reason=reason,
        )
        task.status = changed.status
        task.status_reason = changed.status_reason
        await self.tasks.save(task)
        return task

    async def check_in(
        self,
        student_id: UUID,
        task_id: UUID,
        *,
        content: str,
        actual_hours: float,
        proof_url: str | None,
        idempotency_key: str,
    ) -> TaskCheckInRecord:
        async with self.tasks.lock:
            existing = await self.tasks.get_checkin_by_key(student_id, idempotency_key)
            if existing:
                return existing
            task = await self._owned(student_id, task_id)
            plan = await self.plans.get(task.plan_version_id)
            if plan is None or plan.status is not PlanStatus.active:
                raise ConflictError("只有当前激活计划的任务可以打卡")
            if not content.strip() or actual_hours <= 0:
                raise ConflictError("打卡内容和实际投入小时必须有效")
            if task.status in {TaskStatus.todo, TaskStatus.delayed}:
                await self.transition(student_id, task.id, TaskStatus.in_progress)
            elif task.status is TaskStatus.abandoned:
                raise ConflictError("已放弃任务不能打卡")
            record = TaskCheckInRecord(
                id=uuid4(),
                student_id=student_id,
                task_id=task.id,
                content=content.strip(),
                actual_hours=actual_hours,
                proof_url=proof_url,
            )
            await self.tasks.save_checkin(record, idempotency_key)
            return record

    async def list_checkins(self, student_id: UUID, task_id: UUID):
        await self._owned(student_id, task_id)
        return await self.tasks.list_checkins(task_id)

    async def _owned(self, student_id: UUID, task_id: UUID):
        task = await self.tasks.get(task_id)
        if task is None or task.student_id != student_id:
            raise ForbiddenError("任务不存在或无权访问")
        return task
