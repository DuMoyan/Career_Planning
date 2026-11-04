from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext, Role, ensure_roles
from app.domain.tasks import TaskStatus
from app.schemas.task import TaskCheckInCreate, TaskTransitionRequest

router = APIRouter(prefix="/tasks", tags=["成长任务"])


def _task_json(task) -> dict:
    return {
        "id": task.id,
        "plan_version_id": task.plan_version_id,
        "source_task_id": task.source_task_id,
        "title": task.title,
        "competency_code": task.competency_code,
        "due_date": task.due_date,
        "weekly_hours": task.weekly_hours,
        "source_refs": task.source_refs,
        "status": task.status,
        "status_reason": task.status_reason,
    }


def _checkin_json(checkin) -> dict:
    return {
        "id": checkin.id,
        "task_id": checkin.task_id,
        "content": checkin.content,
        "actual_hours": checkin.actual_hours,
        "proof_url": checkin.proof_url,
        "created_at": checkin.created_at,
    }


@router.get("")
async def list_tasks(
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
    week_start: date | None = None,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
) -> list[dict]:
    ensure_roles(context, {Role.student})
    items = await request.app.state.task_service.list(
        context.user_id, week_start=week_start, status=task_status
    )
    return [_task_json(item) for item in items]


@router.post("/{task_id}/transition")
async def transition_task(
    task_id: UUID,
    payload: TaskTransitionRequest,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    return _task_json(
        await request.app.state.task_service.transition(
            context.user_id,
            task_id,
            TaskStatus(payload.status),
            reason=payload.reason,
        )
    )


@router.post("/{task_id}/check-ins", status_code=status.HTTP_201_CREATED)
async def check_in(
    task_id: UUID,
    payload: TaskCheckInCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> dict:
    checkin = await request.app.state.task_service.check_in(
        context.user_id,
        task_id,
        content=payload.content,
        actual_hours=payload.actual_hours,
        proof_url=str(payload.proof_url) if payload.proof_url else None,
        idempotency_key=idempotency_key,
    )
    return _checkin_json(checkin)


@router.get("/{task_id}/check-ins")
async def list_checkins(
    task_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> list[dict]:
    items = await request.app.state.task_service.list_checkins(context.user_id, task_id)
    return [_checkin_json(item) for item in items]
