from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext, Role
from app.schemas.consent import GrantCreate, GrantResponse
from app.services.grants import GrantService

router = APIRouter(prefix="/consents", tags=["隐私授权"])


def _service(request: Request) -> GrantService:
    return request.app.state.grant_service


@router.post(
    "/mentor-grants",
    response_model=GrantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_grant(
    payload: GrantCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> GrantResponse:
    if context.role is not Role.student:
        from app.core.errors import ForbiddenError

        raise ForbiddenError("只有学生可以创建共享授权")
    grant = await _service(request).create(
        student_id=context.user_id,
        mentor_id=payload.mentor_id,
        scopes=frozenset(payload.scopes),
        expires_at=payload.expires_at,
    )
    return GrantResponse(
        id=grant.id,
        student_id=grant.student_id,
        mentor_id=grant.mentor_id,
        scopes=sorted(grant.scopes, key=lambda scope: scope.value),
        expires_at=grant.expires_at,
        revoked_at=grant.revoked_at,
    )


@router.delete("/mentor-grants/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_grant(
    grant_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> Response:
    await _service(request).revoke(grant_id, context.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
