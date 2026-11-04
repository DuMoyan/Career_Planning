from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProgressPayload(BaseModel):
    answers: dict[UUID, int]


class RecordResponse(BaseModel):
    id: UUID
    scale_id: UUID
    kind: str
    completed_at: datetime
    visibility: str


class ReportResponse(RecordResponse):
    dimension_scores: dict[str, float]
    top_dimensions: tuple[str, ...]
    scale_version: str
    scoring_version: str
    interpretation_version: str
    disclaimer: str

