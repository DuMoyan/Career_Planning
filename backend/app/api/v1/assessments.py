from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext
from app.schemas.assessment import ProgressPayload, RecordResponse, ReportResponse
from app.services.assessments import AssessmentService

router = APIRouter(prefix="/assessments", tags=["职业测评"])


def _service(request: Request) -> AssessmentService:
    return request.app.state.assessment_service


@router.get("/scales")
async def list_scales(
    request: Request,
    _context: Annotated[AccessContext, Depends(current_access_context)],
) -> list[dict]:
    scales = await _service(request).list_scales()
    return [
        {
            "id": scale.definition.id,
            "name": scale.name,
            "kind": scale.kind,
            "version": scale.definition.version,
            "item_count": len(scale.items),
        }
        for scale in scales
    ]


@router.get("/scales/{scale_id}")
async def get_scale(
    scale_id: UUID,
    request: Request,
    _context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    scale = await _service(request).get_scale(scale_id)
    return {
        "id": scale.definition.id,
        "name": scale.name,
        "kind": scale.kind,
        "version": scale.definition.version,
        "items": [
            {"id": item.id, "dimension": item.dimension, "prompt": item.prompt}
            for item in scale.items
        ],
    }


@router.put("/scales/{scale_id}/progress")
async def save_progress(
    scale_id: UUID,
    payload: ProgressPayload,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    await _service(request).save_progress(context.user_id, scale_id, payload.answers)
    return {"saved": True}


@router.get("/scales/{scale_id}/progress")
async def get_progress(
    scale_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    answers = await _service(request).get_progress(context.user_id, scale_id)
    return {"answers": {str(key): value for key, value in answers.items()}}


@router.post(
    "/scales/{scale_id}/submit",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit(
    scale_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> RecordResponse:
    record = await _service(request).submit(context.user_id, scale_id, idempotency_key)
    return RecordResponse.model_validate(record, from_attributes=True)


@router.get("/records/{record_id}/report", response_model=ReportResponse)
async def get_report(
    record_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> ReportResponse:
    record = await _service(request).get_record(context.user_id, record_id)
    return ReportResponse(
        id=record.id,
        scale_id=record.scale_id,
        kind=record.kind,
        completed_at=record.completed_at,
        visibility=record.visibility,
        dimension_scores=record.score.dimension_scores,
        top_dimensions=record.score.top_dimensions,
        scale_version=record.score.scale_version,
        scoring_version=record.score.scoring_version,
        interpretation_version=record.score.interpretation_version,
        disclaimer=record.score.disclaimer,
    )
