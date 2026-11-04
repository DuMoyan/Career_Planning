from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext, Role, ensure_roles

router = APIRouter(prefix="/mentor", tags=["导师"])


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


def _comment(item) -> dict:
    return {
        "id": item.id,
        "mentor_id": item.mentor_id,
        "student_id": item.student_id,
        "plan_version_id": item.plan_version_id,
        "content": item.content,
        "created_at": item.created_at,
    }


@router.get("/students")
async def students(
    request: Request, context: Annotated[AccessContext, Depends(current_access_context)]
) -> list[dict]:
    ensure_roles(context, {Role.mentor})
    return await request.app.state.mentor_service.list_students(context.user_id)


@router.get("/students/{student_id}")
async def student_detail(
    student_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.mentor})
    return await request.app.state.mentor_service.detail(context.user_id, student_id)


@router.post("/plan-versions/{version_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(
    version_id: UUID,
    payload: CommentCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.mentor})
    return _comment(
        await request.app.state.mentor_service.add_comment(
            context.user_id, version_id, payload.content
        )
    )


@router.get("/plan-versions/{version_id}/comments")
async def comments(
    version_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> list[dict]:
    return [
        _comment(item)
        for item in await request.app.state.mentor_service.list_comments(
            context.user_id, context.role, version_id
        )
    ]
