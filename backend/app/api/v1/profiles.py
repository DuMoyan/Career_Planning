from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profiles import ProfileService

router = APIRouter(prefix="/profiles", tags=["学生档案"])


def _service(request: Request) -> ProfileService:
    return request.app.state.profile_service


@router.get("/me", response_model=ProfileResponse)
async def get_own_profile(
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> ProfileResponse:
    return ProfileResponse.model_validate(
        await _service(request).get(context, context.user_id), from_attributes=True
    )


@router.put("/me", response_model=ProfileResponse)
async def update_own_profile(
    payload: ProfileUpdate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> ProfileResponse:
    return ProfileResponse.model_validate(
        await _service(request).update_own(context, payload), from_attributes=True
    )


@router.get("/{student_id}", response_model=ProfileResponse)
async def get_student_profile(
    student_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> ProfileResponse:
    return ProfileResponse.model_validate(
        await _service(request).get(context, student_id), from_attributes=True
    )

