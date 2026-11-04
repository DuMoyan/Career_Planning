from uuid import UUID

from pydantic import BaseModel, Field


class EvidenceCreate(BaseModel):
    resume_id: UUID | None = None
    competency_code: str = Field(min_length=1, max_length=64)
    demonstrated_level: int = Field(ge=1, le=4)
    description: str = Field(min_length=1, max_length=1000)
