from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext, Role, ensure_roles

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/overview")
async def overview(
    request: Request, context: Annotated[AccessContext, Depends(current_access_context)]
) -> dict:
    ensure_roles(context, {Role.admin})
    return await request.app.state.admin_service.overview()
