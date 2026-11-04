from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class TaskTransitionRequest(BaseModel):
    status: Literal["in_progress", "completed", "delayed", "abandoned"]
    reason: str | None = Field(default=None, max_length=1000)


class TaskCheckInCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    actual_hours: float = Field(gt=0, le=168)
    proof_url: HttpUrl | None = None
