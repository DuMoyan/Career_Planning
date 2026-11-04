from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status

from app.core.dependencies import current_access_context
from app.core.errors import ConflictError
from app.domain.access import AccessContext, Role, ensure_roles
from app.schemas.plan import PlanDraftCreate, PlanDraftUpdate, ReplanActivation
from app.schemas.planning import PlanDraft

router = APIRouter(prefix="/plans", tags=["计划版本"])


def _json(version) -> dict:
    return {
        "id": version.id,
        "career_plan_id": version.career_plan_id,
        "ai_run_id": version.ai_run_id,
        "version": version.version,
        "status": version.status,
        "snapshot": version.snapshot.model_dump(mode="json"),
        "parent_version_id": version.parent_version_id,
        "created_at": version.created_at,
        "activated_at": version.activated_at,
    }


async def _validated_ai_plan(request: Request, student_id: UUID, ai_run_id: UUID) -> PlanDraft:
    run = await request.app.state.ai_run_service.get(student_id, ai_run_id)
    if (
        run.status != "completed"
        or not run.plan_snapshot
        or not run.validation_result
        or not run.validation_result.get("valid")
    ):
        raise ConflictError("规划生成结果尚未完成或未通过校验")
    return PlanDraft.model_validate(run.plan_snapshot)


@router.post("/drafts", status_code=status.HTTP_201_CREATED)
async def create_draft(
    payload: PlanDraftCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.student})
    snapshot = await _validated_ai_plan(request, context.user_id, payload.ai_run_id)
    return _json(
        await request.app.state.plan_service.create_draft(
            context.user_id, payload.ai_run_id, snapshot
        )
    )


@router.get("/history")
async def history(
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> list[dict]:
    return [_json(item) for item in await request.app.state.plan_service.history(context.user_id)]


@router.get("/versions/{version_id}")
async def get_version(
    version_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    return _json(await request.app.state.plan_service.get(context.user_id, version_id))


@router.patch("/versions/{version_id}")
async def update_version(
    version_id: UUID,
    payload: PlanDraftUpdate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    return _json(
        await request.app.state.plan_service.update_draft(
            context.user_id, version_id, payload.snapshot
        )
    )


@router.delete("/versions/{version_id}")
async def discard_version(
    version_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    return _json(await request.app.state.plan_service.discard(context.user_id, version_id))


@router.post("/versions/{version_id}/activate")
async def activate_version(
    version_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> dict:
    return _json(
        await request.app.state.plan_service.activate(context.user_id, version_id, idempotency_key)
    )


@router.post("/versions/{active_id}/replans", status_code=status.HTTP_201_CREATED)
async def create_replan(
    active_id: UUID,
    payload: PlanDraftCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    snapshot = await _validated_ai_plan(request, context.user_id, payload.ai_run_id)
    return _json(
        await request.app.state.plan_service.create_replan(
            context.user_id, active_id, payload.ai_run_id, snapshot
        )
    )


@router.get("/versions/{draft_id}/replan-preview")
async def preview_replan(
    draft_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> list[dict]:
    return await request.app.state.plan_service.preview_replan(context.user_id, draft_id)


@router.post("/versions/{draft_id}/activate-replan")
async def activate_replan(
    draft_id: UUID,
    payload: ReplanActivation,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> dict:
    return _json(
        await request.app.state.plan_service.activate_replan(
            context.user_id, draft_id, payload.migrations, idempotency_key
        )
    )
