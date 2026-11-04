from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext

router = APIRouter(prefix="/resumes", tags=["简历解析"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: Annotated[UploadFile, File()],
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    draft = await request.app.state.resume_service.upload(
        context.user_id, file.filename or "", file.content_type or "", await file.read()
    )
    return {
        "id": draft.id,
        "file_name": draft.file_name,
        "candidates": [
            {"competency_code": item.competency_code, "description": item.description}
            for item in draft.candidates
        ],
    }


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> Response:
    await request.app.state.resume_service.delete(context.user_id, resume_id)
    return Response(status_code=204)
