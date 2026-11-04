from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.grants import GrantScope


class GrantCreate(BaseModel):
    mentor_id: UUID
    scopes: list[GrantScope] = Field(min_length=1)
    expires_at: datetime | None = None


class GrantResponse(BaseModel):
    id: UUID
    student_id: UUID
    mentor_id: UUID
    scopes: list[GrantScope]
    expires_at: datetime
    revoked_at: datetime | None

