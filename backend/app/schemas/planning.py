from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class PlanningGap(BaseModel):
    competency_code: str
    status: Literal["met", "developable_gap", "unknown", "hard_unmet"]
    required_level: int = Field(ge=1, le=4)
    current_level: int | None = Field(default=None, ge=1, le=4)
    source: str


class PlanningContext(BaseModel):
    goal_deadline: date
    weekly_hours: float = Field(gt=0, le=168)
    gaps: list[PlanningGap]
    input_references: dict[str, str]
    preferences: dict[str, list[str]] = Field(default_factory=dict)


class MilestoneDraft(BaseModel):
    title: str
    due_date: date
    acceptance_criteria: list[str]


class TaskDraft(BaseModel):
    title: str
    competency_code: str
    due_date: date
    weekly_hours: float = Field(gt=0, le=168)
    source_refs: list[str]
    is_verification: bool = False


class PlanDraft(BaseModel):
    milestones: list[MilestoneDraft]
    tasks: list[TaskDraft]
    sources: list[str]
    unknowns: list[str]
    risks: list[str]
    generation_mode: Literal["model", "rules"]


class ValidationErrorItem(BaseModel):
    field: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationErrorItem] = Field(default_factory=list)
