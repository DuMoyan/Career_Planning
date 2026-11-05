from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class WeeklyReportCreate(BaseModel):
    week_start: date

    @field_validator("week_start")
    @classmethod
    def require_monday(cls, value: date) -> date:
        if value.weekday() != 0:
            raise ValueError("自然周起点必须是周一")
        return value


class ReportResponseCreate(BaseModel):
    action: Literal["accept", "modify", "reject"]
    text: str | None = Field(default=None, max_length=2000)
