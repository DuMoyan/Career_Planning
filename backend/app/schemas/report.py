from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class WeeklyReportCreate(BaseModel):
    week_start: date


class ReportResponseCreate(BaseModel):
    action: Literal["accept", "modify", "reject"]
    text: str | None = Field(default=None, max_length=2000)
