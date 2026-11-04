from dataclasses import dataclass, replace
from enum import StrEnum
from uuid import UUID

from app.core.errors import ConflictError
from app.domain.plans import PlanStatus


class TaskStatus(StrEnum):
    todo = "todo"
    in_progress = "in_progress"
    completed = "completed"
    delayed = "delayed"
    abandoned = "abandoned"


@dataclass(frozen=True, slots=True)
class TaskState:
    id: UUID
    status: TaskStatus
    plan_status: PlanStatus
    check_in_ids: tuple[UUID, ...] = ()
    status_reason: str | None = None


_ALLOWED = {
    TaskStatus.todo: {TaskStatus.in_progress, TaskStatus.abandoned},
    TaskStatus.in_progress: {TaskStatus.completed, TaskStatus.delayed, TaskStatus.abandoned},
    TaskStatus.delayed: {TaskStatus.in_progress, TaskStatus.completed, TaskStatus.abandoned},
    TaskStatus.completed: set(),
    TaskStatus.abandoned: set(),
}


def transition_task(task: TaskState, target: TaskStatus, *, reason: str | None = None) -> TaskState:
    if task.plan_status is not PlanStatus.active:
        raise ConflictError("只有当前激活计划的任务可以修改")
    if target not in _ALLOWED[task.status]:
        raise ConflictError(f"任务不能从 {task.status} 转换为 {target}")
    normalized_reason = reason.strip() if reason else None
    if target in {TaskStatus.delayed, TaskStatus.abandoned} and not normalized_reason:
        raise ConflictError("延期或放弃任务必须填写原因")
    return replace(task, status=target, status_reason=normalized_reason)
