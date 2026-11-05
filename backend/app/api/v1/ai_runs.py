import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext, Role, ensure_roles
from app.services.ai_runs import serialize_run

router = APIRouter(prefix="/plans/generations", tags=["规划生成"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_generation(
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.student})
    run = await request.app.state.ai_run_service.create(context.user_id)
    scheduler = getattr(request.app.state, "schedule_ai_run", None)
    if scheduler is not None and run.status == "running":
        scheduler(run.id, context.user_id)
    return serialize_run(run)


@router.get("/{run_id}")
async def get_generation(
    run_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    return serialize_run(await request.app.state.ai_run_service.get(context.user_id, run_id))


@router.post("/{run_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_generation(
    run_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.student})
    run = await request.app.state.ai_run_service.retry(context.user_id, run_id)
    scheduler = getattr(request.app.state, "schedule_ai_run", None)
    if scheduler is not None and run.status == "running":
        scheduler(run.id, context.user_id)
    return serialize_run(run)


@router.get("/{run_id}/events")
async def generation_events(
    run_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> StreamingResponse:
    events = await request.app.state.ai_run_service.events(context.user_id, run_id)

    async def stream():
        for event_name, payload in events:
            yield f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
