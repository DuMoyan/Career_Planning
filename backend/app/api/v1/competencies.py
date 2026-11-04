from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext
from app.schemas.competency import EvidenceCreate

router = APIRouter(prefix="/competencies", tags=["能力画像"])


@router.get("/evidence")
async def list_evidence(
    request: Request, context: Annotated[AccessContext, Depends(current_access_context)]
) -> list[dict]:
    items = await request.app.state.competency_service.list_evidence(context.user_id)
    return [
        {
            "id": i.id,
            "competency_code": i.competency_code,
            "demonstrated_level": i.demonstrated_level,
            "description": i.description,
            "source_deleted": i.source_deleted,
        }
        for i in items
    ]


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
async def add_evidence(
    payload: EvidenceCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    item = await request.app.state.competency_service.add_evidence(context.user_id, payload)
    return {
        "id": item.id,
        "competency_code": item.competency_code,
        "source_deleted": item.source_deleted,
    }


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_profile(
    request: Request, context: Annotated[AccessContext, Depends(current_access_context)]
) -> dict:
    profile = await request.app.state.competency_service.create_profile(context.user_id)
    return {
        "id": profile.id,
        "version": profile.version,
        "data_completeness": profile.snapshot.data_completeness,
        "dimensions": {
            code: {
                "level": item.level,
                "evidence_count": item.evidence_count,
                "evidence_ids": item.evidence_ids,
            }
            for code, item in profile.snapshot.dimensions.items()
        },
    }
