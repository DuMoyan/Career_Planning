from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    department: str | None = Field(default=None, max_length=64)
    major: str | None = Field(default=None, max_length=64)
    grade_level: str | None = Field(default=None, max_length=16)
    gpa: float | None = Field(default=None, ge=0, le=5)
    available_hours: float = Field(default=0, ge=0, le=168)
    constraints: dict[str, Any] = Field(default_factory=dict)


class ProfileResponse(ProfileUpdate):
    student_id: UUID

