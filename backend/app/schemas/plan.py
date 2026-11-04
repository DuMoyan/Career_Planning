from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.planning import PlanDraft


class PlanDraftCreate(BaseModel):
    ai_run_id: UUID


class PlanDraftUpdate(BaseModel):
    snapshot: PlanDraft


class ReplanActivation(BaseModel):
    migrations: dict[UUID, Literal["continue", "replace", "cancel"]]
