from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TargetComparisonRequest(BaseModel):
    target_ids: list[UUID] = Field(min_length=2, max_length=3)

    @field_validator("target_ids")
    @classmethod
    def require_distinct_targets(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("目标岗位不能重复")
        return value


class GoalCreate(BaseModel):
    target_id: UUID
    deadline: date
    weekly_hours: int | None = Field(default=None, ge=1, le=168)
    constraints: str | None = Field(default=None, max_length=1000)
    primary: bool = False
